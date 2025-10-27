# Copyright (c) 2025, sammish.thundiyil@gmail.com and contributors
# For license information, please see license.txt

"""
Scheduled Tasks for Oropendola AI
Handles background jobs like quota reset, billing, health checks, etc.
"""

import frappe
from frappe.utils import today, add_days, now


def reset_daily_quotas():
	"""
	Reset daily quotas for all active subscriptions.
	Runs daily at 00:00 UTC.
	"""
	try:
		frappe.logger().info("Starting daily quota reset...")
		
		# Get all active subscriptions
		subscriptions = frappe.get_all(
			"AI Subscription",
			filters={"status": ["in", ["Active", "Trial"]]},
			fields=["name", "daily_quota_limit"]
		)
		
		count = 0
		for sub in subscriptions:
			subscription = frappe.get_doc("AI Subscription", sub.name)
			subscription.reset_daily_quota()
			count += 1
		
		frappe.logger().info(f"Daily quota reset completed for {count} subscriptions")
		
	except Exception as e:
		frappe.log_error(f"Failed to reset daily quotas: {str(e)}", "Quota Reset Error")


def check_expired_subscriptions():
	"""
	Check for expired subscriptions and update their status.
	Runs hourly.
	"""
	try:
		frappe.logger().info("Checking expired subscriptions...")
		
		# Get subscriptions that should be expired
		subscriptions = frappe.get_all(
			"AI Subscription",
			filters={
				"status": ["in", ["Active", "Trial"]],
				"end_date": ["<", today()]
			},
			fields=["name"]
		)
		
		count = 0
		for sub in subscriptions:
			subscription = frappe.get_doc("AI Subscription", sub.name)
			subscription.status = "Expired"
			subscription.save(ignore_permissions=True)
			
			# Revoke API key
			if subscription.api_key_link:
				api_key = frappe.get_doc("AI API Key", subscription.api_key_link)
				api_key.revoke("Subscription expired")
			
			count += 1
		
		frappe.db.commit()
		frappe.logger().info(f"Marked {count} subscriptions as expired")
		
	except Exception as e:
		frappe.log_error(f"Failed to check expired subscriptions: {str(e)}", "Expiry Check Error")


def perform_health_checks():
	"""
	Perform health checks on all active model endpoints.
	Runs every 5 minutes.
	"""
	try:
		frappe.logger().info("Performing model health checks...")
		
		models = frappe.get_all(
			"AI Model Profile",
			filters={"is_active": 1},
			fields=["name"]
		)
		
		for model_name in models:
			model = frappe.get_doc("AI Model Profile", model_name.name)
			health_result = model.perform_health_check()
			
			frappe.logger().info(
				f"Model {model.model_name}: {health_result['status']} "
				f"({health_result.get('latency_ms', 'N/A')}ms)"
			)
		
		frappe.logger().info(f"Health checks completed for {len(models)} models")
		
	except Exception as e:
		frappe.log_error(f"Failed to perform health checks: {str(e)}", "Health Check Error")


def generate_billing_invoices():
	"""
	Generate billing invoices for subscriptions.
	Runs daily.
	"""
	try:
		frappe.logger().info("Generating billing invoices...")
		
		# Get subscriptions due for billing
		subscriptions = frappe.get_all(
			"AI Subscription",
			filters={
				"status": ["in", ["Active", "Trial"]],
				"next_billing_date": ["<=", today()],
				"auto_renew": 1
			},
			fields=["name", "customer", "plan"]
		)
		
		count = 0
		for sub in subscriptions:
			# Get usage summary
			usage_summary = frappe.get_doc_import("AI Usage Log").get_usage_summary(
				sub.customer,
				start_date=add_days(today(), -30),
				end_date=today()
			)
			
			# Create invoice
			invoice = frappe.get_doc_import("AI Invoice").create_usage_invoice(
				sub.name,
				usage_summary
			)
			
			frappe.logger().info(f"Created invoice {invoice.name} for subscription {sub.name}")
			count += 1
		
		frappe.logger().info(f"Generated {count} billing invoices")
		
	except Exception as e:
		frappe.log_error(f"Failed to generate billing invoices: {str(e)}", "Billing Error")


def sync_redis_usage_to_db():
	"""
	Sync usage data from Redis to database.
	Runs every 5 minutes to batch write usage logs.
	"""
	try:
		import redis
		import os
		import json
		
		redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
		r = redis.from_url(redis_url, decode_responses=True)
		
		# Get all usage logs from Redis stream
		stream_key = "usage_logs"
		
		# Read from stream
		entries = r.xrange(stream_key, count=1000)
		
		if not entries:
			return
		
		frappe.logger().info(f"Syncing {len(entries)} usage logs from Redis to DB...")
		
		for entry_id, entry_data in entries:
			try:
				# Create usage log in database
				log_data = json.loads(entry_data.get("data", "{}"))
				
				frappe.get_doc({
					"doctype": "AI Usage Log",
					**log_data
				}).insert(ignore_permissions=True)
				
				# Remove from stream after successful insert
				r.xdel(stream_key, entry_id)
				
			except Exception as log_error:
				frappe.log_error(f"Failed to sync usage log {entry_id}: {str(log_error)}")
		
		frappe.db.commit()
		frappe.logger().info(f"Successfully synced {len(entries)} usage logs")
		
	except Exception as e:
		frappe.log_error(f"Failed to sync Redis usage to DB: {str(e)}", "Redis Sync Error")


def cleanup_old_usage_logs():
	"""
	Archive or delete old usage logs (older than 90 days).
	Runs daily.
	"""
	try:
		from frappe.utils import add_days
		
		frappe.logger().info("Cleaning up old usage logs...")
		
		cutoff_date = add_days(today(), -90)
		
		# Delete logs older than 90 days
		frappe.db.sql("""
			DELETE FROM `tabAI Usage Log`
			WHERE timestamp < %s
		""", (cutoff_date,))
		
		frappe.db.commit()
		frappe.logger().info("Old usage logs cleanup completed")
		
	except Exception as e:
		frappe.log_error(f"Failed to cleanup old logs: {str(e)}", "Cleanup Error")


def send_quota_alerts():
	"""
	Send alerts to customers when quota is running low.
	Runs hourly.
	"""
	try:
		frappe.logger().info("Checking for quota alerts...")
		
		# Get subscriptions with low quota
		subscriptions = frappe.get_all(
			"AI Subscription",
			filters={
				"status": "Active",
				"daily_quota_limit": [">", 0]
			},
			fields=["name", "customer", "daily_quota_limit", "daily_quota_remaining", "billing_email"]
		)
		
		count = 0
		for sub in subscriptions:
			if sub.daily_quota_remaining and sub.daily_quota_limit:
				usage_percent = (1 - (sub.daily_quota_remaining / sub.daily_quota_limit)) * 100
				
				# Alert at 80% usage
				if usage_percent >= 80:
					# Send email
					frappe.sendmail(
						recipients=[sub.billing_email or frappe.get_value("Customer", sub.customer, "email_id")],
						subject=f"AI Subscription Quota Alert - {sub.name}",
						message=f"""
						<p>Dear Customer,</p>
						<p>Your AI subscription quota is running low:</p>
						<ul>
							<li>Daily Limit: {sub.daily_quota_limit} requests</li>
							<li>Remaining: {sub.daily_quota_remaining} requests</li>
							<li>Usage: {usage_percent:.1f}%</li>
						</ul>
						<p>Consider upgrading your plan for unlimited requests.</p>
						"""
					)
					count += 1
		
		frappe.logger().info(f"Sent {count} quota alert emails")
		
	except Exception as e:
		frappe.log_error(f"Failed to send quota alerts: {str(e)}", "Quota Alert Error")

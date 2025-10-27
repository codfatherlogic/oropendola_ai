# Copyright (c) 2025, sammish.thundiyil@gmail.com and contributors
# For license information, please see license.txt

"""
Subscription Management API Endpoints
Provides REST APIs for creating, managing, and querying subscriptions.
"""

import frappe
from frappe import _
import secrets
import hashlib


@frappe.whitelist(allow_guest=False)
def create_subscription(customer, plan_id, billing_email=None):
	"""
	Create a new subscription for a customer.
	
	Args:
		customer (str): Customer ID
		plan_id (str): Plan ID
		billing_email (str, optional): Billing email address
		
	Returns:
		dict: Subscription details with API key
	"""
	try:
		# Validate plan exists and is active
		plan = frappe.get_doc("AI Plan", plan_id)
		if not plan.is_active:
			frappe.throw(_("Selected plan is not active"))
		
		# Check if customer exists
		if not frappe.db.exists("Customer", customer):
			frappe.throw(_("Customer does not exist"))
		
		# Create subscription
		subscription = frappe.get_doc({
			"doctype": "AI Subscription",
			"customer": customer,
			"plan": plan_id,
			"status": "Trial" if plan.is_trial else "Active",
			"billing_email": billing_email or frappe.session.user
		})
		
		subscription.insert(ignore_permissions=True)
		frappe.db.commit()
		
		# Retrieve the one-time API key from cache
		raw_api_key = subscription.get_raw_api_key()
		
		# Create invoice
		invoice = frappe.get_doc_import("AI Invoice").create_subscription_invoice(subscription.name)
		
		return {
			"success": True,
			"subscription_id": subscription.name,
			"api_key": raw_api_key,  # Only shown once!
			"api_key_warning": "Store this API key securely. It will not be shown again.",
			"plan": plan_id,
			"status": subscription.status,
			"start_date": subscription.start_date,
			"end_date": subscription.end_date,
			"daily_quota": subscription.daily_quota_limit,
			"invoice_id": invoice.name,
			"amount_due": invoice.total_amount
		}
		
	except Exception as e:
		frappe.log_error(f"Failed to create subscription: {str(e)}", "Subscription API Error")
		return {
			"success": False,
			"error": str(e)
		}


@frappe.whitelist(allow_guest=False)
def get_subscription(subscription_id):
	"""
	Get subscription details.
	
	Args:
		subscription_id (str): Subscription ID
		
	Returns:
		dict: Subscription details
	"""
	try:
		subscription = frappe.get_doc("AI Subscription", subscription_id)
		
		# Check permissions
		if subscription.customer != frappe.db.get_value("Customer", {"email": frappe.session.user}):
			if not frappe.has_permission("AI Subscription", "read", subscription_id):
				frappe.throw(_("Insufficient permissions"))
		
		return {
			"success": True,
			"subscription": {
				"id": subscription.name,
				"customer": subscription.customer,
				"plan": subscription.plan,
				"status": subscription.status,
				"start_date": subscription.start_date,
				"end_date": subscription.end_date,
				"daily_quota_limit": subscription.daily_quota_limit,
				"daily_quota_remaining": subscription.daily_quota_remaining,
				"total_usage": subscription.total_usage,
				"total_requests": subscription.total_requests,
				"priority_score": subscription.priority_score,
				"api_key_prefix": subscription.api_key_link
			}
		}
		
	except Exception as e:
		return {
			"success": False,
			"error": str(e)
		}


@frappe.whitelist(allow_guest=False)
def cancel_subscription(subscription_id, reason=None):
	"""
	Cancel a subscription.
	
	Args:
		subscription_id (str): Subscription ID
		reason (str, optional): Cancellation reason
		
	Returns:
		dict: Cancellation status
	"""
	try:
		subscription = frappe.get_doc("AI Subscription", subscription_id)
		
		# Check permissions
		if not frappe.has_permission("AI Subscription", "write", subscription_id):
			frappe.throw(_("Insufficient permissions"))
		
		subscription.cancel_subscription(reason)
		
		return {
			"success": True,
			"message": "Subscription cancelled successfully"
		}
		
	except Exception as e:
		return {
			"success": False,
			"error": str(e)
		}


@frappe.whitelist(allow_guest=False)
def get_usage_stats(subscription_id, start_date=None, end_date=None):
	"""
	Get usage statistics for a subscription.
	
	Args:
		subscription_id (str): Subscription ID
		start_date (str, optional): Start date (YYYY-MM-DD)
		end_date (str, optional): End date (YYYY-MM-DD)
		
	Returns:
		dict: Usage statistics
	"""
	try:
		subscription = frappe.get_doc("AI Subscription", subscription_id)
		
		# Check permissions
		if not frappe.has_permission("AI Subscription", "read", subscription_id):
			frappe.throw(_("Insufficient permissions"))
		
		# Get usage logs
		filters = {"subscription": subscription_id}
		if start_date:
			filters["timestamp"] = [">=", start_date]
		if end_date:
			filters["timestamp"] = ["<=", end_date]
		
		logs = frappe.get_all(
			"AI Usage Log",
			filters=filters,
			fields=["model", "status", "request_cost_units", "latency_ms", "timestamp"]
		)
		
		# Aggregate stats
		stats = {
			"total_requests": len(logs),
			"successful_requests": len([l for l in logs if l.status == "Success"]),
			"failed_requests": len([l for l in logs if l.status != "Success"]),
			"total_cost_units": sum(l.request_cost_units for l in logs),
			"avg_latency_ms": sum(l.latency_ms or 0 for l in logs) / len(logs) if logs else 0,
			"by_model": {},
			"by_status": {}
		}
		
		# Group by model
		for log in logs:
			if log.model not in stats["by_model"]:
				stats["by_model"][log.model] = 0
			stats["by_model"][log.model] += 1
			
			if log.status not in stats["by_status"]:
				stats["by_status"][log.status] = 0
			stats["by_status"][log.status] += 1
		
		return {
			"success": True,
			"subscription_id": subscription_id,
			"stats": stats
		}
		
	except Exception as e:
		return {
			"success": False,
			"error": str(e)
		}


@frappe.whitelist(allow_guest=False)
def list_plans():
	"""
	List all available subscription plans.
	
	Returns:
		dict: List of available plans
	"""
	try:
		plans = frappe.get_all(
			"AI Plan",
			filters={"is_active": 1},
			fields=["plan_id", "title", "description", "price", "currency",
			        "duration_days", "requests_limit_per_day", "priority_score", "is_trial"]
		)
		
		# Get features for each plan
		for plan in plans:
			features = frappe.get_all(
				"AI Plan Feature",
				filters={"parent": plan.plan_id, "enabled": 1},
				fields=["feature_name"]
			)
			plan["features"] = [f.feature_name for f in features]
			
			models = frappe.get_all(
				"AI Plan Model Access",
				filters={"parent": plan.plan_id, "is_allowed": 1},
				fields=["model_name"]
			)
			plan["models"] = [m.model_name for m in models]
		
		return {
			"success": True,
			"plans": plans
		}
		
	except Exception as e:
		return {
			"success": False,
			"error": str(e)
		}


@frappe.whitelist(allow_guest=False)
def regenerate_api_key(subscription_id):
	"""
	Regenerate API key for a subscription.
	Revokes old key and creates new one.
	
	Args:
		subscription_id (str): Subscription ID
		
	Returns:
		dict: New API key (shown once)
	"""
	try:
		subscription = frappe.get_doc("AI Subscription", subscription_id)
		
		# Check permissions
		if not frappe.has_permission("AI Subscription", "write", subscription_id):
			frappe.throw(_("Insufficient permissions"))
		
		# Revoke old API key
		if subscription.api_key_link:
			old_key = frappe.get_doc("AI API Key", subscription.api_key_link)
			old_key.revoke("Regenerated by user")
		
		# Generate new API key
		raw_key = secrets.token_urlsafe(32)
		key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
		
		new_key_doc = frappe.get_doc({
			"doctype": "AI API Key",
			"customer": subscription.customer,
			"subscription": subscription.name,
			"key_hash": key_hash,
			"key_prefix": raw_key[:8],
			"status": "Active",
			"created_by": frappe.session.user
		})
		new_key_doc.insert(ignore_permissions=True)
		
		# Update subscription
		subscription.db_set("api_key_link", new_key_doc.name)
		frappe.db.commit()
		
		return {
			"success": True,
			"api_key": raw_key,
			"warning": "Store this API key securely. It will not be shown again."
		}
		
	except Exception as e:
		return {
			"success": False,
			"error": str(e)
		}


@frappe.whitelist(allow_guest=True)
def get_monthly_budget_stats(api_key):
	"""
	Get monthly budget statistics for a user.
	
	Args:
		api_key (str): User's API key
		
	Returns:
		dict: Monthly budget statistics
	"""
	try:
		# Validate API key and get subscription
		key_hash = hashlib.sha256(api_key.encode()).hexdigest()
		
		api_key_doc = frappe.get_all(
			"AI API Key",
			filters={"key_hash": key_hash, "status": "Active"},
			fields=["subscription"],
			limit=1
		)
		
		if not api_key_doc:
			return {
				"success": False,
				"error": "Invalid API key"
			}
		
		subscription = frappe.get_doc("AI Subscription", api_key_doc[0].subscription)
		
		# Get budget stats
		stats = subscription.get_monthly_budget_stats()
		
		return {
			"success": True,
			"budget_stats": stats
		}
		
	except Exception as e:
		frappe.log_error(f"Failed to get budget stats: {str(e)}", "Budget Stats API Error")
		return {
			"success": False,
			"error": str(e)
		}

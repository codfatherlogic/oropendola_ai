# Copyright (c) 2025, sammish.thundiyil@gmail.com and contributors
# For license information, please see license.txt

"""
Subscription Renewal API
Handles subscription renewals, extensions, and lifecycle management
"""

import frappe
from frappe import _
from frappe.utils import today, add_days, nowdate, getdate
from datetime import datetime


@frappe.whitelist()
def renew_subscription(plan_id: str = None):
	"""
	Renew or extend user's subscription
	
	Scenarios handled:
	1. Expired subscription - Creates new subscription with same or different plan
	2. Active subscription - Extends end_date and creates renewal invoice
	3. No subscription - Creates new subscription
	
	Args:
		plan_id (str): Plan ID to renew/subscribe to (optional - uses current plan if not provided)
		
	Returns:
		dict: Renewal result with invoice details
	"""
	try:
		user = frappe.session.user
		
		if user == "Guest":
			frappe.throw(_("Please login to renew subscription"))
		
		# Get user's current/most recent subscription
		subscriptions = frappe.get_all(
			"AI Subscription",
			filters={"user": user},
			fields=["name", "plan", "status", "end_date", "start_date"],
			order_by="modified desc",
			limit=1
		)
		
		if not subscriptions:
			# No subscription exists - create new one
			return create_new_subscription(user, plan_id)
		
		current_sub = subscriptions[0]
		
		# Use current plan if no plan_id provided
		if not plan_id:
			plan_id = current_sub["plan"]
		
		# Get plan details
		plan = frappe.get_doc("AI Plan", plan_id)
		
		if not plan.is_active:
			frappe.throw(_("This plan is not available"))
		
		# Handle different scenarios based on current status
		if current_sub["status"] in ["Active", "Trial"]:
			# Scenario 2: Active subscription - extend it
			return extend_active_subscription(current_sub["name"], plan)
		
		elif current_sub["status"] == "Expired":
			# Scenario 3: Expired subscription - create new subscription
			return renew_expired_subscription(user, plan, current_sub)
		
		else:
			# Cancelled, Suspended, Past Due - create new subscription
			return create_new_subscription(user, plan_id)
			
	except Exception as e:
		frappe.log_error(message=str(e), title="Renew Subscription Error")
		return {
			"success": False,
			"error": str(e)
		}


def create_new_subscription(user, plan_id):
	"""Create brand new subscription"""
	from oropendola_ai.oropendola_ai.api.payment import create_subscription_and_invoice
	
	result = create_subscription_and_invoice(plan_id)
	
	if result.get("success"):
		result["renewal_type"] = "new"
		
	return result


def extend_active_subscription(subscription_id, plan):
	"""
	Extend active subscription by adding duration to end_date
	and creating renewal invoice
	"""
	try:
		subscription = frappe.get_doc("AI Subscription", subscription_id)
		
		# Check if user is trying to change plan
		if subscription.plan != plan.name:
			# Plan change requires creating new subscription after current ends
			return {
				"success": False,
				"error": "Cannot change plan while subscription is active. Current subscription will end on {}. Please renew with new plan after expiration.".format(subscription.end_date),
				"suggestion": "wait_for_expiration",
				"current_end_date": subscription.end_date
			}
		
		# Calculate new end date (extend from current end_date, not today)
		current_end = getdate(subscription.end_date)
		new_end_date = add_days(current_end, plan.duration_days) if (plan.duration_days and plan.duration_days > 0) else None
		
		# Create renewal invoice
		invoice = frappe.get_doc({
			"doctype": "AI Invoice",
			"customer": subscription.user,
			"subscription": subscription.name,
			"plan": plan.name,
			"status": "Pending",
			"invoice_date": today(),
			"due_date": add_days(today(), 7),
			"period_start": add_days(current_end, 1),  # Next period starts day after current ends
			"period_end": new_end_date,
			"billing_type": "Renewal",
			"total_amount": plan.price,
			"base_plan_amount": plan.price,
			"currency": plan.currency or "INR",
			"payment_gateway": "PayU"
		})
		invoice.insert(ignore_permissions=True)
		
		# Update subscription end_date (will be applied after payment)
		# Store the new end date in a custom field or handle in payment callback
		subscription.db_set("next_billing_date", add_days(current_end, 1))
		
		frappe.db.commit()
		
		return {
			"success": True,
			"renewal_type": "extension",
			"subscription_id": subscription.name,
			"invoice_id": invoice.name,
			"current_end_date": str(current_end),
			"new_end_date": str(new_end_date),
			"amount": float(plan.price),
			"currency": plan.currency or "INR",
			"is_free": float(plan.price or 0) == 0,
			"message": f"Your subscription will be extended to {new_end_date} after payment"
		}
		
	except Exception as e:
		frappe.log_error(f"Extend subscription error: {str(e)}", "Subscription Extension Error")
		raise


def renew_expired_subscription(user, plan, old_subscription):
	"""
	Create new subscription after expiration
	Old subscription remains as historical record
	"""
	try:
		start_date = today()
		end_date = add_days(start_date, plan.duration_days) if (plan.duration_days and plan.duration_days > 0) else None
		
		# Create new subscription (not extending old one)
		subscription = frappe.get_doc({
			"doctype": "AI Subscription",
			"user": user,
			"plan": plan.name,
			"status": "Pending",
			"start_date": start_date,
			"end_date": end_date,
			"billing_email": frappe.db.get_value("User", user, "email"),
			"daily_quota_limit": plan.requests_limit_per_day,
			"daily_quota_remaining": plan.requests_limit_per_day,
			"created_by_user": user
		})
		subscription.insert(ignore_permissions=True)
		
		# Create invoice for new subscription
		invoice = frappe.get_doc({
			"doctype": "AI Invoice",
			"customer": user,
			"subscription": subscription.name,
			"plan": plan.name,
			"status": "Pending",
			"invoice_date": today(),
			"due_date": add_days(today(), 7),
			"period_start": start_date,
			"period_end": end_date,
			"billing_type": "Renewal",
			"total_amount": plan.price,
			"base_plan_amount": plan.price,
			"currency": plan.currency or "INR",
			"payment_gateway": "PayU"
		})
		invoice.insert(ignore_permissions=True)
		
		frappe.db.commit()
		
		return {
			"success": True,
			"renewal_type": "new_after_expiration",
			"subscription_id": subscription.name,
			"invoice_id": invoice.name,
			"old_subscription_id": old_subscription["name"],
			"amount": float(plan.price),
			"currency": plan.currency or "INR",
			"is_free": float(plan.price or 0) == 0,
			"message": "New subscription created. Previous subscription has expired."
		}
		
	except Exception as e:
		frappe.log_error(f"Renew expired subscription error: {str(e)}", "Expired Renewal Error")
		raise


@frappe.whitelist()
def get_subscription_status():
	"""
	Get detailed subscription status for current user
	
	Returns:
		dict: Subscription status with renewal options
	"""
	try:
		user = frappe.session.user
		
		if user == "Guest":
			return {
				"success": True,
				"has_subscription": False,
				"can_renew": False,
				"is_guest": True
			}
		
		# Get current subscription
		subscriptions = frappe.get_all(
			"AI Subscription",
			filters={"user": user},
			fields=["name", "plan", "status", "end_date", "start_date"],
			order_by="modified desc",
			limit=1
		)
		
		if not subscriptions:
			return {
				"success": True,
				"has_subscription": False,
				"can_renew": False,
				"can_subscribe": True
			}
		
		sub = subscriptions[0]
		plan = frappe.get_doc("AI Plan", sub["plan"])
		
		# Calculate days remaining
		days_remaining = 0
		if sub["end_date"]:
			end_date = getdate(sub["end_date"])
			today_date = getdate(today())
			days_remaining = (end_date - today_date).days
		
		# Determine renewal eligibility
		can_renew = True
		renewal_type = None
		
		if sub["status"] in ["Active", "Trial"]:
			renewal_type = "extension"
			# Allow renewal 7 days before expiration
			can_renew = days_remaining <= 7
		elif sub["status"] == "Expired":
			renewal_type = "new_subscription"
			can_renew = True
		else:
			renewal_type = "new_subscription"
			can_renew = True
		
		return {
			"success": True,
			"has_subscription": True,
			"subscription": {
				"id": sub["name"],
				"plan_name": plan.title,
				"plan_id": plan.name,
				"status": sub["status"],
				"start_date": sub["start_date"],
				"end_date": sub["end_date"],
				"days_remaining": days_remaining
			},
			"can_renew": can_renew,
			"renewal_type": renewal_type,
			"renewal_message": get_renewal_message(sub["status"], days_remaining)
		}
		
	except Exception as e:
		frappe.log_error(message=str(e), title="Get Subscription Status Error")
		return {
			"success": False,
			"error": str(e)
		}


def get_renewal_message(status, days_remaining):
	"""Get user-friendly renewal message"""
	if status in ["Active", "Trial"]:
		if days_remaining <= 0:
			return "Your subscription has expired. Renew now to continue using our services."
		elif days_remaining <= 7:
			return f"Your subscription expires in {days_remaining} days. Renew now to extend your access."
		else:
			return f"Your subscription is active and will expire in {days_remaining} days."
	elif status == "Expired":
		return "Your subscription has expired. Renew now to regain access."
	else:
		return "Subscribe to a plan to get started."


@frappe.whitelist()
def apply_payment_to_subscription(invoice_id: str):
	"""
	Apply successful payment to subscription (called by payment callback)
	
	Handles:
	- New subscriptions: Activate and set dates
	- Renewals/Extensions: Extend end_date
	- Free plans: Immediate activation
	"""
	try:
		invoice = frappe.get_doc("AI Invoice", invoice_id)
		subscription = frappe.get_doc("AI Subscription", invoice.subscription)
		
		# Mark invoice as paid
		invoice.db_set("status", "Paid")
		invoice.db_set("paid_date", nowdate())
		
		# Update subscription based on billing type
		if invoice.billing_type == "Renewal" and subscription.status == "Active":
			# Extension: Add duration to current end_date
			plan = frappe.get_doc("AI Plan", subscription.plan)
			current_end = getdate(subscription.end_date)
			new_end_date = add_days(current_end, plan.duration_days) if (plan.duration_days and plan.duration_days > 0) else None
			
			subscription.db_set("end_date", new_end_date)
			subscription.db_set("amount_paid", (subscription.amount_paid or 0) + invoice.total_amount)
			subscription.db_set("last_payment_date", nowdate())
			
		else:
			# New subscription or renewal after expiration: Activate
			subscription.db_set("amount_paid", invoice.total_amount)
			subscription.db_set("last_payment_date", nowdate())

			# Ensure dates are set
			if not subscription.start_date:
				subscription.db_set("start_date", today())
			if not subscription.end_date:
				plan = frappe.get_doc("AI Plan", subscription.plan)
				subscription.db_set("end_date", add_days(subscription.start_date, plan.duration_days))

			# Reload subscription to get latest data
			subscription.reload()

			# Activate subscription (sets status, quota, and creates API key)
			subscription.activate_after_payment()
		
		frappe.db.commit()
		
		return {
			"success": True,
			"subscription_id": subscription.name,
			"status": "Active"
		}
		
	except Exception as e:
		frappe.log_error(f"Apply payment error: {str(e)}", "Payment Application Error")
		return {
			"success": False,
			"error": str(e)
		}

# Copyright (c) 2025, sammish.thundiyil@gmail.com and contributors
# For license information, please see license.txt

"""
Simplified User API for Frappe User-based authentication
Replaces complex AI Customer auth flow with standard Frappe User
"""

import frappe
from frappe import _


@frappe.whitelist()
def get_my_api_key():
	"""
	Get API key for the currently logged-in user.
	User must be authenticated (logged in) to call this.
	
	Returns:
		dict: API key details or error
	"""
	try:
		# Check if user is logged in
		if frappe.session.user == "Guest":
			return {
				"success": False,
				"error": "Authentication required. Please log in."
			}
		
		# Get active subscription for current user
		subscriptions = frappe.get_all(
			"AI Subscription",
			filters={"user": frappe.session.user, "status": ["in", ["Active", "Trial"]]},
			fields=["name", "plan", "status", "api_key_link"],
			limit=1
		)
		
		if not subscriptions:
			return {
				"success": False,
				"error": "No active subscription found. Please subscribe to a plan."
			}
		
		subscription = subscriptions[0]
		
		# Check if API key exists
		if not subscription.api_key_link:
			return {
				"success": False,
				"error": "No API key found. Please contact support."
			}
		
		# Get API key
		api_key = frappe.get_doc("AI API Key", subscription.api_key_link)
		
		# Try to get raw key from cache (only available for 5 minutes after creation)
		cache_key = f"api_key_raw:{subscription.name}"
		raw_key = frappe.cache().get_value(cache_key)
		
		if raw_key:
			# Raw key available - show it
			return {
				"success": True,
				"api_key": raw_key,
				"api_key_prefix": api_key.key_prefix,
				"subscription_id": subscription.name,
				"plan": subscription.plan,
				"status": subscription.status,
				"warning": "⚠️ This is your API key. Store it securely - it will not be shown again!"
			}
		else:
			# Raw key not available - already retrieved
			return {
				"success": True,
				"api_key": None,
				"api_key_prefix": api_key.key_prefix,
				"subscription_id": subscription.name,
				"plan": subscription.plan,
				"status": subscription.status,
				"message": "API key already retrieved. If you've lost it, please regenerate from your dashboard."
			}
		
	except Exception as e:
		frappe.log_error(f"Failed to get API key: {str(e)}", "Get API Key Error")
		return {
			"success": False,
			"error": str(e)
		}


@frappe.whitelist()
def get_my_subscription():
	"""
	Get subscription details for the currently logged-in user.
	
	Returns:
		dict: Subscription details
	"""
	try:
		# Check if user is logged in
		if frappe.session.user == "Guest":
			return {
				"success": False,
				"error": "Authentication required. Please log in."
			}
		
		# Get active subscription
		subscriptions = frappe.get_all(
			"AI Subscription",
			filters={"user": frappe.session.user, "status": ["in", ["Active", "Trial"]]},
			fields=["name", "plan", "status", "start_date", "end_date", "daily_quota_limit",
			        "daily_quota_remaining", "monthly_budget_limit", "monthly_budget_used"],
			limit=1
		)
		
		if not subscriptions:
			return {
				"success": False,
				"error": "No active subscription found."
			}
		
		subscription = subscriptions[0]
		
		# Get plan details
		plan = frappe.get_doc("AI Plan", subscription.plan)
		
		return {
			"success": True,
			"subscription": {
				"id": subscription.name,
				"plan_id": subscription.plan,
				"plan_title": plan.title,
				"status": subscription.status,
				"start_date": subscription.start_date,
				"end_date": subscription.end_date,
				"daily_quota": {
					"limit": subscription.daily_quota_limit,
					"remaining": subscription.daily_quota_remaining
				},
				"monthly_budget": {
					"limit": subscription.monthly_budget_limit,
					"used": subscription.monthly_budget_used,
					"remaining": subscription.monthly_budget_limit - subscription.monthly_budget_used if subscription.monthly_budget_limit else -1
				}
			}
		}
		
	except Exception as e:
		frappe.log_error(f"Failed to get subscription: {str(e)}", "Get Subscription Error")
		return {
			"success": False,
			"error": str(e)
		}


@frappe.whitelist()
def regenerate_api_key():
	"""
	Regenerate API key for the currently logged-in user.
	Revokes old key and creates new one.
	
	Returns:
		dict: New API key
	"""
	try:
		# Check if user is logged in
		if frappe.session.user == "Guest":
			return {
				"success": False,
				"error": "Authentication required. Please log in."
			}
		
		# Get active subscription
		subscriptions = frappe.get_all(
			"AI Subscription",
			filters={"user": frappe.session.user, "status": ["in", ["Active", "Trial"]]},
			fields=["name", "api_key_link"],
			limit=1
		)
		
		if not subscriptions:
			return {
				"success": False,
				"error": "No active subscription found."
			}
		
		subscription = frappe.get_doc("AI Subscription", subscriptions[0].name)
		
		# Revoke old API key
		if subscription.api_key_link:
			old_key = frappe.get_doc("AI API Key", subscription.api_key_link)
			old_key.db_set("status", "Revoked")
			old_key.db_set("revoked_by", frappe.session.user)
			old_key.db_set("revoke_reason", "Regenerated by user")
		
		# Create new API key
		import secrets
		import hashlib
		
		raw_key = secrets.token_urlsafe(32)
		key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
		
		new_key_doc = frappe.get_doc({
			"doctype": "AI API Key",
			"user": frappe.session.user,
			"subscription": subscription.name,
			"key_hash": key_hash,
			"key_prefix": raw_key[:8],
			"status": "Active",
			"created_by": frappe.session.user
		})
		new_key_doc.insert(ignore_permissions=True)
		
		# Update subscription
		subscription.db_set("api_key_link", new_key_doc.name)
		
		# Cache raw key
		cache_key = f"api_key_raw:{subscription.name}"
		frappe.cache().set_value(cache_key, raw_key, expires_in_sec=300)
		
		frappe.db.commit()
		
		return {
			"success": True,
			"api_key": raw_key,
			"api_key_prefix": raw_key[:8],
			"warning": "⚠️ Store this API key securely. It will not be shown again!"
		}
		
	except Exception as e:
		frappe.log_error(f"Failed to regenerate API key: {str(e)}", "Regenerate API Key Error")
		return {
			"success": False,
			"error": str(e)
		}

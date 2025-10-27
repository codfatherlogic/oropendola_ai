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
\t"""
\tGet API key for the currently logged-in user.
\tUser must be authenticated (logged in) to call this.
\t
\tReturns:
\t\tdict: API key details or error
\t"""
\ttry:
\t\t# Check if user is logged in
\t\tif frappe.session.user == "Guest":
\t\t\treturn {
\t\t\t\t"success": False,
\t\t\t\t"error": "Authentication required. Please log in."
\t\t\t}
\t\t
\t\t# Get active subscription for current user
\t\tsubscriptions = frappe.get_all(
\t\t\t"AI Subscription",
\t\t\tfilters={"user": frappe.session.user, "status": ["in", ["Active", "Trial"]]},
\t\t\tfields=["name", "plan", "status", "api_key_link"],
\t\t\tlimit=1
\t\t)
\t\t
\t\tif not subscriptions:
\t\t\treturn {
\t\t\t\t"success": False,
\t\t\t\t"error": "No active subscription found. Please subscribe to a plan."
\t\t\t}
\t\t
\t\tsubscription = subscriptions[0]
\t\t
\t\t# Check if API key exists
\t\tif not subscription.api_key_link:
\t\t\treturn {
\t\t\t\t"success": False,
\t\t\t\t"error": "No API key found. Please contact support."
\t\t\t}
\t\t
\t\t# Get API key
\t\tapi_key = frappe.get_doc("AI API Key", subscription.api_key_link)
\t\t
\t\t# Try to get raw key from cache (only available for 5 minutes after creation)
\t\tcache_key = f"api_key_raw:{subscription.name}"
\t\traw_key = frappe.cache().get_value(cache_key)
\t\t
\t\tif raw_key:
\t\t\t# Raw key available - show it
\t\t\treturn {
\t\t\t\t"success": True,
\t\t\t\t"api_key": raw_key,
\t\t\t\t"api_key_prefix": api_key.key_prefix,
\t\t\t\t"subscription_id": subscription.name,
\t\t\t\t"plan": subscription.plan,
\t\t\t\t"status": subscription.status,
\t\t\t\t"warning": "⚠️ This is your API key. Store it securely - it will not be shown again!"
\t\t\t}
\t\telse:
\t\t\t# Raw key not available - already retrieved
\t\t\treturn {
\t\t\t\t"success": True,
\t\t\t\t"api_key": None,
\t\t\t\t"api_key_prefix": api_key.key_prefix,
\t\t\t\t"subscription_id": subscription.name,
\t\t\t\t"plan": subscription.plan,
\t\t\t\t"status": subscription.status,
\t\t\t\t"message": "API key already retrieved. If you've lost it, please regenerate from your dashboard."
\t\t\t}
\t\t
\texcept Exception as e:
\t\tfrappe.log_error(f"Failed to get API key: {str(e)}", "Get API Key Error")
\t\treturn {
\t\t\t"success": False,
\t\t\t"error": str(e)
\t\t}


@frappe.whitelist()
def get_my_subscription():
\t"""
\tGet subscription details for the currently logged-in user.
\t
\tReturns:
\t\tdict: Subscription details
\t"""
\ttry:
\t\t# Check if user is logged in
\t\tif frappe.session.user == "Guest":
\t\t\treturn {
\t\t\t\t"success": False,
\t\t\t\t"error": "Authentication required. Please log in."
\t\t\t}
\t\t
\t\t# Get active subscription
\t\tsubscriptions = frappe.get_all(
\t\t\t"AI Subscription",
\t\t\tfilters={"user": frappe.session.user, "status": ["in", ["Active", "Trial"]]},
\t\t\tfields=["name", "plan", "status", "start_date", "end_date", "daily_quota_limit",
\t\t\t        "daily_quota_remaining", "monthly_budget_limit", "monthly_budget_used"],
\t\t\tlimit=1
\t\t)
\t\t
\t\tif not subscriptions:
\t\t\treturn {
\t\t\t\t"success": False,
\t\t\t\t"error": "No active subscription found."
\t\t\t}
\t\t
\t\tsubscription = subscriptions[0]
\t\t
\t\t# Get plan details
\t\tplan = frappe.get_doc("AI Plan", subscription.plan)
\t\t
\t\treturn {
\t\t\t"success": True,
\t\t\t"subscription": {
\t\t\t\t"id": subscription.name,
\t\t\t\t"plan_id": subscription.plan,
\t\t\t\t"plan_title": plan.title,
\t\t\t\t"status": subscription.status,
\t\t\t\t"start_date": subscription.start_date,
\t\t\t\t"end_date": subscription.end_date,
\t\t\t\t"daily_quota": {
\t\t\t\t\t"limit": subscription.daily_quota_limit,
\t\t\t\t\t"remaining": subscription.daily_quota_remaining
\t\t\t\t},
\t\t\t\t"monthly_budget": {
\t\t\t\t\t"limit": subscription.monthly_budget_limit,
\t\t\t\t\t"used": subscription.monthly_budget_used,
\t\t\t\t\t"remaining": subscription.monthly_budget_limit - subscription.monthly_budget_used if subscription.monthly_budget_limit else -1
\t\t\t\t}
\t\t\t}
\t\t}
\t\t
\texcept Exception as e:
\t\tfrappe.log_error(f"Failed to get subscription: {str(e)}", "Get Subscription Error")
\t\treturn {
\t\t\t"success": False,
\t\t\t"error": str(e)
\t\t}


@frappe.whitelist()
def regenerate_api_key():
\t"""
\tRegenerate API key for the currently logged-in user.
\tRevokes old key and creates new one.
\t
\tReturns:
\t\tdict: New API key
\t"""
\ttry:
\t\t# Check if user is logged in
\t\tif frappe.session.user == "Guest":
\t\t\treturn {
\t\t\t\t"success": False,
\t\t\t\t"error": "Authentication required. Please log in."
\t\t\t}
\t\t
\t\t# Get active subscription
\t\tsubscriptions = frappe.get_all(
\t\t\t"AI Subscription",
\t\t\tfilters={"user": frappe.session.user, "status": ["in", ["Active", "Trial"]]},
\t\t\tfields=["name", "api_key_link"],
\t\t\tlimit=1
\t\t)
\t\t
\t\tif not subscriptions:
\t\t\treturn {
\t\t\t\t"success": False,
\t\t\t\t"error": "No active subscription found."
\t\t\t}
\t\t
\t\tsubscription = frappe.get_doc("AI Subscription", subscriptions[0].name)
\t\t
\t\t# Revoke old API key
\t\tif subscription.api_key_link:
\t\t\told_key = frappe.get_doc("AI API Key", subscription.api_key_link)
\t\t\told_key.db_set("status", "Revoked")
\t\t\told_key.db_set("revoked_by", frappe.session.user)
\t\t\told_key.db_set("revoke_reason", "Regenerated by user")
\t\t
\t\t# Create new API key
\t\timport secrets
\t\timport hashlib
\t\t
\t\traw_key = secrets.token_urlsafe(32)
\t\tkey_hash = hashlib.sha256(raw_key.encode()).hexdigest()
\t\t
\t\tnew_key_doc = frappe.get_doc({
\t\t\t"doctype": "AI API Key",
\t\t\t"user": frappe.session.user,
\t\t\t"subscription": subscription.name,
\t\t\t"key_hash": key_hash,
\t\t\t"key_prefix": raw_key[:8],
\t\t\t"status": "Active",
\t\t\t"created_by": frappe.session.user
\t\t})
\t\tnew_key_doc.insert(ignore_permissions=True)
\t\t
\t\t# Update subscription
\t\tsubscription.db_set("api_key_link", new_key_doc.name)
\t\t
\t\t# Cache raw key
\t\tcache_key = f"api_key_raw:{subscription.name}"
\t\tfrappe.cache().set_value(cache_key, raw_key, expires_in_sec=300)
\t\t
\t\tfrappe.db.commit()
\t\t
\t\treturn {
\t\t\t"success": True,
\t\t\t"api_key": raw_key,
\t\t\t"api_key_prefix": raw_key[:8],
\t\t\t"warning": "⚠️ Store this API key securely. It will not be shown again!"
\t\t}
\t\t
\texcept Exception as e:
\t\tfrappe.log_error(f"Failed to regenerate API key: {str(e)}", "Regenerate API Key Error")
\t\treturn {
\t\t\t"success": False,
\t\t\t"error": str(e)
\t\t}

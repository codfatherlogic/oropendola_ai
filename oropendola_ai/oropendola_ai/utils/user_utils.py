# Copyright (c) 2025, sammish.thundiyil@gmail.com and contributors
# For license information, please see license.txt

"""
User Utilities
Handles automatic subscription creation and user-related operations
"""

import frappe


def create_default_subscription(user, method):
	"""
	Auto-create AI Subscription when a new Website User signs up.
	Called via hooks.py doc_events.
	
	Args:
		user (Document): User document
		method (str): Event method name
	"""
	# Only for Website Users (not System Users)
	if user.user_type != "Website User":
		return
	
	# Skip if user is disabled
	if not user.enabled:
		return
	
	# Check if subscription already exists
	existing = frappe.db.exists("AI Subscription", {"user": user.name, "status": ["in", ["Active", "Trial"]]})
	if existing:
		frappe.log_error(f"Subscription already exists for user {user.name}", "Auto Subscription")
		return
	
	try:
		# Get free plan (default plan for new users)
		free_plan = frappe.db.get_value("AI Plan", {"plan_id": "free", "is_active": 1})
		
		if not free_plan:
			# If no free plan, get any active trial plan
			free_plan = frappe.db.get_value("AI Plan", {"is_trial": 1, "is_active": 1})
		
		if not free_plan:
			# If still no plan, get first active plan
			free_plan = frappe.get_all("AI Plan", filters={"is_active": 1}, limit=1, pluck="name")
			free_plan = free_plan[0] if free_plan else None
		
		if not free_plan:
			frappe.log_error(f"No active AI Plan found to create subscription for user {user.name}", "Auto Subscription Error")
			return
		
		# Create subscription
		subscription = frappe.get_doc({
			"doctype": "AI Subscription",
			"user": user.name,
			"plan": free_plan,
			"status": "Active",
			"billing_email": user.email
		})
		subscription.insert(ignore_permissions=True)
		frappe.db.commit()
		
		frappe.log_error(
			f"Auto-created subscription {subscription.name} for user {user.name} with plan {free_plan}",
			"Auto Subscription Success"
		)
		
	except Exception as e:
		frappe.log_error(
			f"Failed to create auto subscription for user {user.name}: {str(e)}",
			"Auto Subscription Error"
		)

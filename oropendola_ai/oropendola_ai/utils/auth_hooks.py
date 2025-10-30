# Copyright (c) 2025, sammish.thundiyil@gmail.com and contributors
# For license information, please see license.txt

"""
Authentication hooks to intercept login and enforce redirect logic
"""

import frappe


def validate_auth():
	"""
	Called after successful authentication to set proper redirects.
	This runs AFTER LoginManager.authenticate() succeeds.
	DOES NOT set home_page to avoid redirect issues on public pages.
	"""
	try:
		user = frappe.session.user
		
		# Skip for Guest or Administrator
		if user in ["Guest", "Administrator"]:
			return
		
		# Get user roles
		user_roles = frappe.get_roles(user)
		frappe.logger().info(f"Auth hook - User: {user}, Roles: {user_roles}")
		
		# Check if user has desk access
		has_desk_access = "System Manager" in user_roles or "Administrator" in user_roles
		
		# Just log the user type - don't force redirects
		if not has_desk_access:
			frappe.logger().info(f"Auth hook - Website user {user} authenticated")
		else:
			frappe.logger().info(f"Auth hook - Admin user {user} authenticated")
			
	except Exception as e:
		frappe.logger().error(f"Auth hook error: {str(e)}")
		frappe.log_error(f"Auth hook failed: {str(e)}", "Auth Hook Error")

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
		
		# For website users, force redirect to profile
		if not has_desk_access:
			# Override the default home page
			frappe.local.response["home_page"] = "/my-profile"
			frappe.response["home_page"] = "/my-profile"
			
			# Clear the "No App" message
			frappe.local.response["message"] = "Logged In"
			frappe.response["message"] = "Logged In"
			
			frappe.logger().info(f"Auth hook - Redirecting {user} to /my-profile")
		else:
			# Admin users go to desk
			frappe.local.response["home_page"] = "/app"
			frappe.response["home_page"] = "/app"
			frappe.local.response["message"] = "Logged In"
			frappe.response["message"] = "Logged In"
			
			frappe.logger().info(f"Auth hook - Redirecting {user} to /app")
			
	except Exception as e:
		frappe.logger().error(f"Auth hook error: {str(e)}")
		frappe.log_error(f"Auth hook failed: {str(e)}", "Auth Hook Error")

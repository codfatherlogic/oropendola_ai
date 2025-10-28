# Copyright (c) 2025, sammish.thundiyil@gmail.com and contributors
# For license information, please see license.txt

import frappe

def on_session_creation(login_manager):
	"""
	Called after user session is created.
	Override default desk redirect to keep users on website.
	"""
	# Get logged in user
	user = frappe.session.user
	
	# Don't process for Guest or Administrator
	if user in ["Administrator", "Guest"]:
		return
	
	# Get user roles
	user_roles = frappe.get_roles(user)
	
	# Check if user has desk access
	has_desk_access = "System Manager" in user_roles or "Administrator" in user_roles
	
	# For website users (customers), force redirect to profile dashboard
	if not has_desk_access:
		# Clear any existing redirect
		if hasattr(frappe.local, "response"):
			frappe.local.response["home_page"] = "/my-profile"
		
		# Set redirect location directly
		if hasattr(login_manager, "redirect_to"):
			login_manager.redirect_to = "/my-profile"
		
		# Force the response
		frappe.local.flags.redirect_location = "/my-profile"
		
		# Log for debugging
		frappe.logger().info(f"Session created for website user {user}, redirecting to /my-profile")


def extend_bootinfo(bootinfo):
	"""
	Extend boot info to force website users to homepage.
	"""
	user = frappe.session.user
	
	if user == "Guest":
		return
	
	# Get user roles
	user_roles = frappe.get_roles(user)
	
	# Check if user has desk access
	has_desk_access = "System Manager" in user_roles or "Administrator" in user_roles
	
	# For website users, set home_page to profile dashboard
	if not has_desk_access:
		bootinfo["home_page"] = "/my-profile"
		bootinfo["desk_theme"] = None  # Disable desk theme
		# Remove desk access
		if "modules" in bootinfo:
			bootinfo["modules"] = []
		if "all_apps" in bootinfo:
			bootinfo["all_apps"] = []

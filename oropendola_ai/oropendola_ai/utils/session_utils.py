# Copyright (c) 2025, sammish.thundiyil@gmail.com and contributors
# For license information, please see license.txt

import frappe

def on_session_creation(login_manager):
	"""
	Called after user session is created (after login).
	Set redirect location for website users to /my-profile.
	"""
	user = frappe.session.user
	
	if user == "Guest":
		return
	
	# Get user roles
	user_roles = frappe.get_roles(user)
	
	# Check if user has desk access
	has_desk_access = "System Manager" in user_roles or "Administrator" in user_roles
	
	# For website users, set redirect to profile
	if not has_desk_access:
		# Set the redirect location
		if hasattr(login_manager, "redirect_to"):
			login_manager.redirect_to = "/my-profile"
		frappe.logger().info(f"Session created for website user {user}, will redirect to /my-profile")


def extend_bootinfo(bootinfo):
	"""
	Extend boot info - DON'T set home_page to avoid 'No App' error.
	"""
	user = frappe.session.user
	
	if user == "Guest":
		return
	
	# Get user roles
	user_roles = frappe.get_roles(user)
	
	# Check if user has desk access
	has_desk_access = "System Manager" in user_roles or "Administrator" in user_roles
	
	# For website users, just remove desk access - DON'T set home_page
	if not has_desk_access:
		# Remove desk access modules
		if "modules" in bootinfo:
			bootinfo["modules"] = []
		if "all_apps" in bootinfo:
			bootinfo["all_apps"] = []

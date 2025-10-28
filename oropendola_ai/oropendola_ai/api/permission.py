# Copyright (c) 2025, sammish.thundiyil@gmail.com and contributors
# For license information, please see license.txt

"""
Permission utilities for Oropendola AI app
"""

import frappe


def has_app_permission(app=None):
	"""
	Check if user has permission to access the Oropendola AI app.
	
	Args:
		app (str): App name (optional)
	
	Returns:
		bool: True if user has permission, False otherwise
	"""
	# Allow if user is System Manager or Administrator
	if "System Manager" in frappe.get_roles() or "Administrator" in frappe.get_roles():
		return True
	
	# Allow if user has AI Assistant User role (for accessing AI features)
	if "AI Assistant User" in frappe.get_roles():
		return True
	
	# Deny by default
	return False

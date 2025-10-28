# Copyright (c) 2025, sammish.thundiyil@gmail.com and contributors
# For license information, please see license.txt

import frappe

def get_context(context):
	"""
	Context for VS Code authentication page
	"""
	context.no_cache = 1
	context.show_sidebar = False
	
	# Get session token from query params
	session_token = frappe.form_dict.get('token')
	
	if not session_token:
		frappe.throw("Invalid authentication request")
	
	context.session_token = session_token
	context.title = "VS Code Authentication"
	
	return context

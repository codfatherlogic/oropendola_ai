# Copyright (c) 2025, sammish.thundiyil@gmail.com and contributors
# For license information, please see license.txt

"""
VS Code Authentication Hook
Intercepts requests to VS Code auth endpoints and handles Bearer token authentication
BEFORE Frappe's core auth validation runs
"""

import frappe
from frappe import _


def handle_vscode_auth():
	"""
	Handle VS Code Bearer token authentication before Frappe's core auth runs.
	This allows Bearer tokens to work with allow_guest=True endpoints.
	"""
	# Only process POST requests to VS Code auth endpoints
	if frappe.request.method != "POST":
		return

	# Get the endpoint being called
	cmd = frappe.local.form_dict.get("cmd")

	# List of VS Code endpoints that use Bearer token auth
	vscode_endpoints = [
		"oropendola_ai.oropendola_ai.api.vscode_auth.get_my_profile",
		"oropendola_ai.oropendola_ai.api.vscode_auth.get_subscription_status",
		"oropendola_ai.oropendola_ai.api.vscode_auth.logout",
		"oropendola_ai.oropendola_ai.api.vscode_auth.refresh_token"
	]

	# Check if this is a VS Code auth endpoint
	if cmd not in vscode_endpoints:
		return

	# Get Authorization header
	auth_header = frappe.get_request_header("Authorization")

	if not auth_header or not auth_header.startswith("Bearer "):
		return

	# Extract token
	access_token = auth_header.replace("Bearer ", "")

	# Verify token and get user
	try:
		result = frappe.db.sql("""
			SELECT user
			FROM `tabVS Code Auth Request`
			WHERE access_token = %s AND status = 'Completed'
			LIMIT 1
		""", (access_token,), as_dict=True)

		if result:
			# Valid token - set user session to allow access
			frappe.set_user(result[0].user)
			# Clear the Authorization header so Frappe's auth doesn't see it
			frappe.local.request.headers.environ.pop("HTTP_AUTHORIZATION", None)
	except Exception as e:
		frappe.log_error(f"VS Code auth hook error: {str(e)}", "VS Code Auth Hook")
		pass

# Copyright (c) 2025, sammish.thundiyil@gmail.com and contributors
# For license information, please see license.txt

"""
Custom Authentication for VS Code Extension
Handles Bearer token authentication for VS Code endpoints
"""

import frappe
from frappe import _


def validate():
	"""
	Custom auth validation that runs INSTEAD OF Frappe's default validate_auth()
	when auth_hooks is configured in hooks.py
	"""
	# Get the endpoint being called
	cmd = frappe.local.form_dict.get("cmd")

	# DEBUG: Log every request to understand cmd format
	import sys
	print(f"🔍 AUTH HOOK: cmd={cmd}", file=sys.stderr, flush=True)

	# List of VS Code endpoints that use Bearer token auth
	vscode_endpoints = [
		"oropendola_ai.oropendola_ai.api.vscode_auth.get_my_profile",
		"oropendola_ai.oropendola_ai.api.vscode_auth.get_subscription_status",
		"oropendola_ai.oropendola_ai.api.vscode_auth.logout",
		"oropendola_ai.oropendola_ai.api.vscode_auth.refresh_token"
	]

	# Check if this is a VS Code auth endpoint
	if cmd in vscode_endpoints:
		print(f"🔍 AUTH HOOK: Matched VS Code endpoint!", file=sys.stderr, flush=True)
		# Get Authorization header
		auth_header = frappe.get_request_header("Authorization")

		frappe.logger().info(f"🔐 VS Code auth hook: endpoint={cmd}, has_auth_header={bool(auth_header)}")

		if auth_header and auth_header.startswith("Bearer "):
			# Extract token
			access_token = auth_header.replace("Bearer ", "")
			token_preview = access_token[:20] + "..." if len(access_token) > 20 else access_token

			frappe.logger().info(f"🔐 VS Code auth hook: Validating token {token_preview}")

			# Verify token and get user
			try:
				# Check if DB is available
				if not frappe.db:
					frappe.logger().error("🔐 VS Code auth hook: DB not available yet")
					frappe.throw(_("Authentication service unavailable"), frappe.AuthenticationError)

				result = frappe.db.sql("""
					SELECT user
					FROM `tabVS Code Auth Request`
					WHERE access_token = %s AND status = 'Completed'
					LIMIT 1
				""", (access_token,), as_dict=True)

				frappe.logger().info(f"🔐 VS Code auth hook: Query returned {len(result) if result else 0} results")

				if result:
					# Valid token - set user to bypass Frappe's auth
					user_email = result[0].user
					frappe.logger().info(f"🔐 VS Code auth hook: Setting user to {user_email}")
					frappe.set_user(user_email)
					frappe.logger().info(f"🔐 VS Code auth hook: Auth successful for {user_email}")
					return  # Auth successful, exit early
				else:
					frappe.logger().warning(f"🔐 VS Code auth hook: No matching token found for {token_preview}")

			except Exception as e:
				frappe.logger().error(f"🔐 VS Code auth hook error: {str(e)}")
				frappe.log_error(frappe.get_traceback(), "VS Code Auth Hook Error")
				# Fall through to default auth for invalid tokens

	# For all other endpoints or failed VS Code auth, use Frappe's default HTTP auth
	# Since auth_hooks REPLACES validate_auth entirely, we need to explicitly
	# handle session-based authentication for web requests
	from frappe.auth import HTTPRequest

	# Use Frappe's HTTP authentication for session-based auth (cookies)
	# This handles normal web login, API keys, OAuth tokens, etc.
	http_request = HTTPRequest()

	# The HTTPRequest class handles all standard Frappe authentication:
	# - Session cookies (sid)
	# - API keys (api_key, api_secret)
	# - Token-based auth
	# - OAuth2
	# No need to return anything - authentication is complete

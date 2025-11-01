"""
Custom 404 Not Found Handler
Redirects logged-in users to /features instead of showing 404 error
"""

import frappe
from frappe import _


def handle_404(exception=None):
	"""
	Custom 404 handler that redirects logged-in users to /features
	For guests, show the default 404 page

	Args:
		exception: The exception that triggered the 404 (optional)
	"""
	# Check if user is logged in
	user = frappe.session.user if hasattr(frappe, 'session') else None

	if user and user != "Guest":
		# User is logged in - perform redirect
		# Use frappe.respond_as_web_page with redirect
		frappe.local.response['type'] = 'redirect'
		frappe.local.response['location'] = '/features'
		frappe.local.response['http_status_code'] = 302
		return

	# User is not logged in - show custom 404 page using frappe's method
	frappe.respond_as_web_page(
		_("Page Not Found"),
		_("The page you are looking for has gone missing. Let's get you back on track."),
		http_status_code=404,
		indicator_color='red'
	)

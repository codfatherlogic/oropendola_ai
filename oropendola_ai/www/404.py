"""
Custom 404 Page Handler
Redirects logged-in users to /features
"""

import frappe


def get_context(context):
	"""
	Set context for 404 page
	Redirect logged-in users to /features
	"""
	context.http_status_code = 404

	# Check if user is logged in
	if frappe.session.user and frappe.session.user != "Guest":
		# User is logged in - redirect to features
		frappe.local.flags.redirect_location = "/features"
		raise frappe.Redirect

	# User is guest - continue rendering 404 page
	context.title = "Page Not Found"
	return context

# Copyright (c) 2025, sammish.thundiyil@gmail.com and contributors
# For license information, please see license.txt

import frappe

def get_context(context):
	"""
	Context for custom login page with social login support
	"""
	context.no_cache = 1
	context.show_sidebar = False
	
	# If user is already logged in, redirect to home (website, not desk)
	if frappe.session.user != "Guest":
		redirect_to = frappe.form_dict.get("redirect-to") or "/"
		# Ensure we don't redirect to desk
		if redirect_to.startswith("/app") or redirect_to.startswith("/desk"):
			redirect_to = "/"
		frappe.local.flags.redirect_location = redirect_to
		raise frappe.Redirect
	
	# Add social login configuration
	try:
		social_providers = frappe.db.get_all(
			'Social Login Key',
			filters={'enabled': 1},
			fields=['provider']
		)
		context.social_login_enabled = len(social_providers) > 0
		context.social_providers_count = len(social_providers)
	except Exception:
		context.social_login_enabled = False
		context.social_providers_count = 0
	
	context.title = "Sign In - Oropendola AI"
	
	return context

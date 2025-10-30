import frappe

def get_context(context):
	"""Set cache control headers for features page"""
	frappe.response["type"] = "page"
	frappe.local.response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
	frappe.local.response.headers["Pragma"] = "no-cache"
	frappe.local.response.headers["Expires"] = "0"
	return context

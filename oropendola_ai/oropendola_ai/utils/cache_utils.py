# Copyright (c) 2025, sammish.thundiyil@gmail.com and contributors
# For license information, please see license.txt

"""
Cache Control Utilities
Prevents aggressive browser caching in development mode
"""

import frappe
from frappe import _


def set_cache_headers():
	"""
	Set appropriate cache headers for HTTP responses.
	In development: Disable caching for easier testing
	In production: Enable caching with versioning
	"""
	try:
		# Skip for API calls (they handle their own caching)
		if frappe.request and frappe.request.path.startswith("/api/"):
			# Still set no-cache for development
			if frappe.conf.get("developer_mode"):
				if hasattr(frappe.local, "response") and frappe.local.response:
					if not hasattr(frappe.local.response, "headers") or frappe.local.response.headers is None:
						frappe.local.response.headers = {}
					frappe.local.response.headers.update({
						"Cache-Control": "no-cache, no-store, must-revalidate, max-age=0, s-maxage=0",
						"Pragma": "no-cache",
						"Expires": "0"
					})
			return
		
		# Skip for assets in production only
		if frappe.request and frappe.request.path.startswith("/assets/"):
			if not frappe.conf.get("developer_mode"):
				return
		
		# Check if response object exists and has headers
		if not hasattr(frappe.local, "response") or frappe.local.response is None:
			return
		
		# Initialize headers dict if it doesn't exist
		if not hasattr(frappe.local.response, "headers") or frappe.local.response.headers is None:
			frappe.local.response.headers = {}
		
		# Check if we're in development mode
		is_dev_mode = frappe.conf.get("developer_mode") or frappe.conf.get("developer_mode") == 1
		
		if is_dev_mode:
			# Development mode: Aggressive no caching
			frappe.local.response.headers.update({
				"Cache-Control": "no-cache, no-store, must-revalidate, max-age=0, s-maxage=0, no-transform, proxy-revalidate",
				"Pragma": "no-cache",
				"Expires": "0",
				"Last-Modified": __import__('datetime').datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT'),
				"X-Content-Type-Options": "nosniff",
				"X-Frame-Options": "SAMEORIGIN",
				"ETag": f"\"dev-{int(__import__('time').time())}-{__import__('random').randint(1000, 9999)}\"",
				"Vary": "*"
			})
		else:
			# Production mode: Cache for 1 hour
			frappe.local.response.headers.update({
				"Cache-Control": "public, max-age=3600, must-revalidate",
				"Vary": "Accept-Encoding"
			})
	except Exception as e:
		# Silently fail to not break requests
		frappe.log_error(f"Cache headers error: {str(e)}", "Cache Utils")


def get_cache_buster():
	"""
	Get cache-busting version string.
	Uses app version or timestamp.
	
	Returns:
		str: Version string for cache busting
	"""
	try:
		# Get app version from hooks
		from oropendola_ai import __version__
		return __version__
	except:
		# Fallback to timestamp
		import time
		return str(int(time.time()))

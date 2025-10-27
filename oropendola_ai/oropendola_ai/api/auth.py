# Copyright (c) 2025, sammish.thundiyil@gmail.com and contributors
# For license information, please see license.txt

"""
Authentication API Endpoints for VS Code Extension
Handles OAuth-style authentication flow with email verification
"""

import frappe
from frappe import _
import secrets
import hashlib


@frappe.whitelist(allow_guest=True)
def initiate_signin(email, redirect_uri=None):
	"""
	Initiate sign-in flow from VS Code extension.
	Returns OAuth-style authorization URL.
	
	Args:
		email (str): User's email address
		redirect_uri (str, optional): Redirect URI after auth
		
	Returns:
		dict: Authorization URL and state
	"""
	try:
		# Generate state token for CSRF protection
		state = secrets.token_urlsafe(32)
		
		# Store state in cache (5 minutes)
		cache_key = f"auth_state:{state}"
		frappe.cache().set_value(cache_key, {
			"email": email,
			"redirect_uri": redirect_uri
		}, expires_in_sec=300)
		
		# Build authorization URL
		base_url = frappe.utils.get_url()
		auth_url = f"{base_url}/api/method/oropendola_ai.oropendola_ai.api.auth.authenticate"
		
		# Return auth URL with state
		return {
			"success": True,
			"auth_url": f"{auth_url}?email={email}&state={state}",
			"state": state,
			"message": "Please open the URL in your browser to complete sign-in"
		}
		
	except Exception as e:
		frappe.log_error(f"Failed to initiate sign-in: {str(e)}", "Auth Error")
		return {
			"success": False,
			"error": str(e)
		}


@frappe.whitelist(allow_guest=True)
def authenticate(email, state=None):
	"""
	Main authentication endpoint.
	Handles both existing users (sign-in) and new users (sign-up).
	
	Args:
		email (str): User's email address
		state (str, optional): State token from initiate_signin
		
	Returns:
		HTTP Redirect to appropriate page
	"""
	try:
		# Validate state token if provided
		if state:
			cache_key = f"auth_state:{state}"
			cached_data = frappe.cache().get_value(cache_key)
			
			if not cached_data or cached_data.get("email") != email:
				frappe.throw("Invalid or expired authentication request")
		
		# Check if customer exists
		existing_customer = frappe.db.exists("AI Customer", {"email": email})
		
		if existing_customer:
			# Existing user - sign in
			customer = frappe.get_doc("AI Customer", existing_customer)
			
			if not customer.email_verified:
				# User exists but email not verified
				# Resend verification email
				customer.send_verification_email()
				
				frappe.local.response["type"] = "redirect"
				frappe.local.response["location"] = f"{frappe.utils.get_url()}/verification-pending?email={email}"
				return
			
			# Email verified - check if Frappe User exists
			if not customer.user:
				customer.create_frappe_user()
			
			# Log user in
			frappe.local.login_manager.login_as(customer.user)
			
			# Redirect to dashboard
			frappe.local.response["type"] = "redirect"
			frappe.local.response["location"] = f"{frappe.utils.get_url()}/dashboard"
		
		else:
			# New user - sign up
			frappe.local.response["type"] = "redirect"
			frappe.local.response["location"] = f"{frappe.utils.get_url()}/signup?email={email}&state={state}"
	
	except Exception as e:
		frappe.log_error(f"Authentication failed: {str(e)}", "Auth Error")
		frappe.local.response["type"] = "redirect"
		frappe.local.response["location"] = f"{frappe.utils.get_url()}/auth-error?message={str(e)}"


@frappe.whitelist(allow_guest=True)
def signup(email, customer_name, state=None):
	"""
	Create new customer account.
	Sends verification email automatically.
	
	Args:
		email (str): User's email address
		customer_name (str): Customer's name
		state (str, optional): State token from initiate_signin
		
	Returns:
		dict: Signup result
	"""
	try:
		# Validate state token if provided
		if state:
			cache_key = f"auth_state:{state}"
			cached_data = frappe.cache().get_value(cache_key)
			
			if not cached_data or cached_data.get("email") != email:
				return {
					"success": False,
					"error": "Invalid or expired authentication request"
				}
		
		# Check if customer already exists
		if frappe.db.exists("AI Customer", {"email": email}):
			return {
				"success": False,
				"error": "Email already registered. Please sign in instead."
			}
		
		# Create customer
		customer = frappe.get_doc({
			"doctype": "AI Customer",
			"customer_name": customer_name,
			"email": email,
			"status": "Pending Verification"
		})
		customer.insert(ignore_permissions=True)
		frappe.db.commit()
		
		# Verification email is sent automatically in after_insert
		
		return {
			"success": True,
			"customer_id": customer.name,
			"message": f"Account created! Verification email sent to {email}",
			"verification_pending": True
		}
		
	except Exception as e:
		frappe.log_error(f"Signup failed: {str(e)}", "Signup Error")
		return {
			"success": False,
			"error": str(e)
		}


@frappe.whitelist(allow_guest=True)
def verify_email(token):
	"""
	Verify email address using token from email.
	
	Args:
		token (str): Verification token
		
	Returns:
		HTTP Redirect to success/error page
	"""
	try:
		# Hash token
		token_hash = hashlib.sha256(token.encode()).hexdigest()
		
		# Find customer with this token
		customers = frappe.get_all(
			"AI Customer",
			filters={"verification_token": token_hash, "email_verified": 0},
			fields=["name"],
			limit=1
		)
		
		if not customers:
			frappe.local.response["type"] = "redirect"
			frappe.local.response["location"] = f"{frappe.utils.get_url()}/verification-error?reason=invalid_token"
			return
		
		# Verify email
		customer = frappe.get_doc("AI Customer", customers[0].name)
		verified = customer.verify_email(token)
		
		if verified:
			# Success - redirect to dashboard
			frappe.local.response["type"] = "redirect"
			frappe.local.response["location"] = f"{frappe.utils.get_url()}/verification-success?email={customer.email}"
		else:
			# Token expired or invalid
			frappe.local.response["type"] = "redirect"
			frappe.local.response["location"] = f"{frappe.utils.get_url()}/verification-error?reason=expired_token"
	
	except Exception as e:
		frappe.log_error(f"Email verification failed: {str(e)}", "Verification Error")
		frappe.local.response["type"] = "redirect"
		frappe.local.response["location"] = f"{frappe.utils.get_url()}/verification-error?reason=error"


@frappe.whitelist(allow_guest=True)
def resend_verification(email):
	"""
	Resend verification email to user.
	
	Args:
		email (str): User's email address
		
	Returns:
		dict: Result
	"""
	try:
		# Find customer
		customer_id = frappe.db.exists("AI Customer", {"email": email})
		
		if not customer_id:
			return {
				"success": False,
				"error": "Email not found"
			}
		
		customer = frappe.get_doc("AI Customer", customer_id)
		
		if customer.email_verified:
			return {
				"success": False,
				"error": "Email already verified"
			}
		
		# Resend verification
		customer.send_verification_email()
		
		return {
			"success": True,
			"message": f"Verification email resent to {email}"
		}
		
	except Exception as e:
		frappe.log_error(f"Failed to resend verification: {str(e)}", "Resend Error")
		return {
			"success": False,
			"error": str(e)
		}


@frappe.whitelist(allow_guest=False)
def get_api_key():
	"""
	Get API key for authenticated user.
	Returns existing key or creates new one.
	
	Returns:
		dict: API key details
	"""
	try:
		# Get customer for current user
		customer_id = frappe.db.get_value("AI Customer", {"user": frappe.session.user})
		
		if not customer_id:
			return {
				"success": False,
				"error": "No customer account found"
			}
		
		customer = frappe.get_doc("AI Customer", customer_id)
		
		# Get or create subscription (use free plan by default)
		free_plan = frappe.db.get_value("AI Plan", {"plan_id": "free"})
		if not free_plan:
			# Get first available plan
			free_plan = frappe.get_all("AI Plan", filters={"is_active": 1}, limit=1, pluck="name")
			free_plan = free_plan[0] if free_plan else None
		
		if not free_plan:
			return {
				"success": False,
				"error": "No active plans available"
			}
		
		subscription = customer.get_or_create_subscription(free_plan)
		
		# Get API key
		if subscription.api_key_link:
			api_key = frappe.get_doc("AI API Key", subscription.api_key_link)
			
			# Try to get raw key from cache
			cache_key = f"api_key_raw:{subscription.name}"
			raw_key = frappe.cache().get_value(cache_key)
			
			return {
				"success": True,
				"api_key": raw_key if raw_key else None,
				"api_key_prefix": api_key.key_prefix,
				"subscription_id": subscription.name,
				"plan": subscription.plan,
				"warning": "API key shown once. Store it securely." if raw_key else "API key already retrieved. Contact support to regenerate."
			}
		
		return {
			"success": False,
			"error": "No API key found. Please contact support."
		}
		
	except Exception as e:
		frappe.log_error(f"Failed to get API key: {str(e)}", "API Key Error")
		return {
			"success": False,
			"error": str(e)
		}


@frappe.whitelist(allow_guest=True)
def check_auth_status(state):
	"""
	Check if authentication is complete (for polling from VS Code).
	
	Args:
		state (str): State token from initiate_signin
		
	Returns:
		dict: Auth status and API key if complete
	"""
	try:
		# Check if state exists in cache
		cache_key = f"auth_state:{state}"
		cached_data = frappe.cache().get_value(cache_key)
		
		if not cached_data:
			return {
				"success": False,
				"status": "expired",
				"message": "Authentication session expired"
			}
		
		email = cached_data.get("email")
		
		# Check if customer exists and is verified
		customer_id = frappe.db.get_value("AI Customer", {"email": email}, ["name", "email_verified"], as_dict=True)
		
		if not customer_id:
			return {
				"success": True,
				"status": "pending",
				"message": "Waiting for signup"
			}
		
		if not customer_id.email_verified:
			return {
				"success": True,
				"status": "verification_pending",
				"message": "Waiting for email verification"
			}
		
		# Customer verified - get API key
		customer = frappe.get_doc("AI Customer", customer_id.name)
		
		# Get subscription
		subscription = frappe.get_all(
			"AI Subscription",
			filters={"customer": customer.name, "status": ["in", ["Active", "Trial"]]},
			fields=["name", "api_key_link"],
			limit=1
		)
		
		if not subscription:
			return {
				"success": True,
				"status": "no_subscription",
				"message": "Please create a subscription"
			}
		
		# Get API key from cache
		cache_key = f"api_key_raw:{subscription[0].name}"
		raw_key = frappe.cache().get_value(cache_key)
		
		if raw_key:
			# Clear auth state
			frappe.cache().delete_value(f"auth_state:{state}")
			
			return {
				"success": True,
				"status": "complete",
				"api_key": raw_key,
				"message": "Authentication complete"
			}
		
		return {
			"success": True,
			"status": "key_unavailable",
			"message": "API key already retrieved. Please contact support."
		}
		
	except Exception as e:
		frappe.log_error(f"Failed to check auth status: {str(e)}", "Auth Status Error")
		return {
			"success": False,
			"error": str(e)
		}

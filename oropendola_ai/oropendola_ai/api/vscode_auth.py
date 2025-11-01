# Copyright (c) 2025, sammish.thundiyil@gmail.com and contributors
# For license information, please see license.txt

"""
VS Code Extension Authentication API
Handles OAuth-like authentication flow for VS Code extension
"""

import frappe
from frappe import _
from frappe.utils import now, add_to_date, cint, get_datetime
import secrets
import hashlib
import json
from datetime import datetime, timedelta
from urllib.parse import quote


@frappe.whitelist(allow_guest=True)
def initiate_auth():
	"""
	Initiate VS Code authentication flow

	Returns:
		dict: Auth request details including login URL
	"""
	try:
		# Generate unique auth request ID
		auth_request_id = frappe.generate_hash(length=20)

		# Create auth request document
		auth_request = frappe.get_doc({
			"doctype": "VS Code Auth Request",
			"auth_request_id": auth_request_id,
			"status": "Pending",
			"expires_at": add_to_date(now(), minutes=5)
		})
		auth_request.insert(ignore_permissions=True)
		frappe.db.commit()

		# Generate login URL
		login_url = f"{frappe.utils.get_url()}/vscode-login?auth_request={auth_request_id}"

		return {
			"success": True,
			"auth_request_id": auth_request_id,
			"login_url": login_url,
			"expires_in": 300,  # 5 minutes
			"poll_interval": 2  # Poll every 2 seconds
		}

	except Exception as e:
		frappe.log_error(f"VS Code auth initiation error: {str(e)}", "VS Code Auth Error")
		return {
			"success": False,
			"error": str(e)
		}


@frappe.whitelist(allow_guest=True)
def check_auth_status(auth_request_id: str):
	"""
	Check if user has completed login

	Args:
		auth_request_id: Auth request ID

	Returns:
		dict: Auth status with tokens if completed
	"""
	try:
		# Get auth request by auth_request_id field
		auth_requests = frappe.get_all(
			"VS Code Auth Request",
			filters={"auth_request_id": auth_request_id},
			fields=["name"],
			limit=1,
			ignore_permissions=True
		)

		if not auth_requests:
			return {
				"success": False,
				"error": "Invalid authentication request ID"
			}

		auth_request = frappe.get_doc("VS Code Auth Request", auth_requests[0].name, ignore_permissions=True)

		# Check if expired
		if get_datetime(auth_request.expires_at) < get_datetime(now()):
			auth_request.db_set("status", "Expired")
			return {
				"success": False,
				"status": "expired",
				"error": "Authentication request expired. Please try again."
			}

		# Check status
		if auth_request.status == "Pending":
			return {
				"success": True,
				"status": "pending",
				"message": "Waiting for user to complete login"
			}

		elif auth_request.status == "Completed":
			# Get user details
			user = frappe.get_doc("User", auth_request.user)

			# Return tokens and user info
			return {
				"success": True,
				"status": "completed",
				"access_token": auth_request.access_token,
				"refresh_token": auth_request.refresh_token,
				"token_type": "Bearer",
				"expires_in": 2592000,  # 30 days
				"user": {
					"email": user.email,
					"full_name": user.full_name,
					"user_image": user.user_image or ""
				}
			}

		else:
			return {
				"success": False,
				"status": auth_request.status.lower(),
				"error": f"Authentication {auth_request.status.lower()}"
			}

	except frappe.DoesNotExistError:
		return {
			"success": False,
			"error": "Invalid authentication request ID"
		}
	except Exception as e:
		frappe.log_error(f"VS Code auth status check error: {str(e)}", "VS Code Auth Error")
		return {
			"success": False,
			"error": str(e)
		}


@frappe.whitelist(allow_guest=True)
def complete_auth(auth_request_id: str):
	"""
	Complete authentication after user login (called by website)

	Args:
		auth_request_id: Auth request ID

	Returns:
		HTML page or redirect
	"""
	try:
		# Get auth request by auth_request_id field
		auth_requests = frappe.get_all(
			"VS Code Auth Request",
			filters={"auth_request_id": auth_request_id},
			fields=["name"],
			limit=1,
			ignore_permissions=True
		)

		if not auth_requests:
			frappe.local.response["type"] = "redirect"
			frappe.local.response["location"] = "/vscode-auth-error?type=invalid"
			return

		auth_request = frappe.get_doc("VS Code Auth Request", auth_requests[0].name, ignore_permissions=True)

		# Check if expired
		if get_datetime(auth_request.expires_at) < get_datetime(now()):
			frappe.local.response["type"] = "redirect"
			frappe.local.response["location"] = "/vscode-auth-error?type=expired"
			return

		# Check if user is logged in
		if frappe.session.user == "Guest":
			# Redirect to login with return URL
			frappe.local.response["type"] = "redirect"
			frappe.local.response["location"] = f"/login?redirect-to=/api/method/oropendola_ai.oropendola_ai.api.vscode_auth.complete_auth?auth_request_id={auth_request_id}"
			return

		# Generate access and refresh tokens
		access_token = generate_access_token(frappe.session.user)
		refresh_token = generate_refresh_token(frappe.session.user)

		# Update auth request
		auth_request.db_set("status", "Completed")
		auth_request.db_set("user", frappe.session.user)
		auth_request.db_set("access_token", access_token)
		auth_request.db_set("refresh_token", refresh_token)
		auth_request.db_set("completed_at", now())

		frappe.db.commit()

		# Get user details for success page
		user = frappe.get_doc("User", frappe.session.user)
		user_name = quote(user.full_name or user.email)
		user_email = quote(user.email)

		# Redirect to dark-themed success page with user info
		frappe.local.response["type"] = "redirect"
		frappe.local.response["location"] = f"/vscode-auth-success?name={user_name}&email={user_email}"

	except frappe.DoesNotExistError:
		frappe.local.response["type"] = "redirect"
		frappe.local.response["location"] = "/vscode-auth-error?type=invalid"
	except Exception as e:
		frappe.log_error(f"VS Code auth completion error: {str(e)}", "VS Code Auth Error")
		frappe.local.response["type"] = "redirect"
		frappe.local.response["location"] = f"/vscode-auth-error?type=error&message={quote(str(e))}"


@frappe.whitelist(allow_guest=True)
def refresh_token(refresh_token: str):
	"""
	Refresh access token using refresh token

	Args:
		refresh_token: Refresh token

	Returns:
		dict: New access token
	"""
	try:
		# Find auth request with this refresh token
		auth_requests = frappe.get_all(
			"VS Code Auth Request",
			filters={"refresh_token": refresh_token, "status": "Completed"},
			fields=["name", "user"]
		)

		if not auth_requests:
			return {
				"success": False,
				"error": "Invalid refresh token"
			}

		auth_request = auth_requests[0]

		# Generate new access token
		new_access_token = generate_access_token(auth_request.user)

		# Update auth request
		frappe.db.set_value("VS Code Auth Request", auth_request.name, "access_token", new_access_token)

		# Clear document cache to ensure fresh reads
		frappe.clear_document_cache("VS Code Auth Request", auth_request.name)

		frappe.db.commit()

		return {
			"success": True,
			"access_token": new_access_token,
			"token_type": "Bearer",
			"expires_in": 2592000  # 30 days
		}

	except Exception as e:
		frappe.log_error(f"Token refresh error: {str(e)}", "VS Code Auth Error")
		return {
			"success": False,
			"error": str(e)
		}


@frappe.whitelist(allow_guest=True)
def logout():
	"""
	Logout and revoke tokens

	Returns:
		dict: Success message
	"""
	try:
		# Get access token from Authorization header
		access_token = get_token_from_header()

		if access_token:
			# Find and revoke auth request
			auth_requests = frappe.get_all(
				"VS Code Auth Request",
				filters={"access_token": access_token},
				fields=["name"]
			)

			for req in auth_requests:
				frappe.db.set_value("VS Code Auth Request", req.name, "status", "Revoked")

		frappe.db.commit()

		return {
			"success": True,
			"message": "Successfully logged out"
		}

	except Exception as e:
		frappe.log_error(f"Logout error: {str(e)}", "VS Code Auth Error")
		return {
			"success": False,
			"error": str(e)
		}


@frappe.whitelist(allow_guest=True)
def get_subscription_status():
	"""
	Get current user's subscription status

	Returns:
		dict: Subscription details
	"""
	try:
		# Authenticate user from token
		user = authenticate_from_token()

		if not user:
			frappe.throw(_("Unauthorized"), frappe.AuthenticationError)

		# Get active subscription
		subscriptions = frappe.get_all(
			"AI Subscription",
			filters={
				"user": user,
				"status": ["in", ["Active", "Trial", "Expired", "Cancelled"]]
			},
			fields=["*"],
			order_by="creation desc",
			limit=1
		)

		if not subscriptions:
			return {
				"success": True,
				"subscription": None,
				"message": "No active subscription found"
			}

		sub = subscriptions[0]

		# Calculate days remaining
		if sub.end_date:
			end_datetime = get_datetime(sub.end_date)
			now_datetime = get_datetime(now())
			days_remaining = (end_datetime - now_datetime).days

			if days_remaining < 0:
				expired_days_ago = abs(days_remaining)
			else:
				expired_days_ago = 0
		else:
			days_remaining = -1  # Unlimited
			expired_days_ago = 0

		# Get plan details
		plan = frappe.get_doc("AI Plan", sub.plan) if sub.plan else None

		return {
			"success": True,
			"subscription": {
				"id": sub.name,
				"status": sub.status,
				"plan_name": plan.plan_name if plan else "Unknown",
				"plan_type": plan.duration_label if plan else "",
				"start_date": str(sub.start_date),
				"end_date": str(sub.end_date) if sub.end_date else None,
				"is_active": sub.status in ["Active", "Trial"],
				"is_trial": sub.status == "Trial",
				"days_remaining": days_remaining if days_remaining >= 0 else -1,
				"auto_renew": cint(sub.auto_renew),
				"expired_days_ago": expired_days_ago if expired_days_ago > 0 else None,
				"quota": {
					"daily_limit": cint(sub.daily_quota_limit),
					"daily_remaining": cint(sub.daily_quota_remaining),
					"usage_percent": round((1 - (cint(sub.daily_quota_remaining) / cint(sub.daily_quota_limit))) * 100, 2) if cint(sub.daily_quota_limit) > 0 else 0
				}
			}
		}

	except frappe.AuthenticationError:
		frappe.local.response["http_status_code"] = 401
		return {
			"success": False,
			"error": "Unauthorized"
		}
	except Exception as e:
		frappe.log_error(f"Get subscription status error: {str(e)}", "VS Code Auth Error")
		return {
			"success": False,
			"error": str(e)
		}


@frappe.whitelist()
def check_feature_access(feature: str = "ai_completion"):
	"""
	Check if user can access specific features

	Args:
		feature: Feature name

	Returns:
		dict: Access status
	"""
	try:
		# Authenticate user from token
		user = authenticate_from_token()

		if not user:
			frappe.throw(_("Unauthorized"), frappe.AuthenticationError)

		# Get subscription status
		status_result = get_subscription_status()

		if not status_result.get("success"):
			return status_result

		subscription = status_result.get("subscription")

		# Check access
		if not subscription:
			return {
				"success": True,
				"has_access": False,
				"subscription_status": "None",
				"message": "No subscription found. Please subscribe to access this feature.",
				"renewal_url": f"{frappe.utils.get_url()}/pricing"
			}

		if subscription["is_active"]:
			# Check quota
			if subscription["quota"]["daily_remaining"] <= 0:
				return {
					"success": True,
					"has_access": False,
					"subscription_status": subscription["status"],
					"quota_remaining": 0,
					"message": "Daily quota exhausted. Quota will reset tomorrow."
				}

			return {
				"success": True,
				"has_access": True,
				"subscription_status": subscription["status"],
				"quota_remaining": subscription["quota"]["daily_remaining"],
				"message": "Access granted"
			}
		else:
			return {
				"success": True,
				"has_access": False,
				"subscription_status": subscription["status"],
				"message": "Subscription expired. Please renew to continue.",
				"renewal_url": f"{frappe.utils.get_url()}/pricing"
			}

	except frappe.AuthenticationError:
		frappe.local.response["http_status_code"] = 401
		return {
			"success": False,
			"error": "Unauthorized"
		}
	except Exception as e:
		frappe.log_error(f"Check feature access error: {str(e)}", "VS Code Auth Error")
		return {
			"success": False,
			"error": str(e)
		}


@frappe.whitelist()
def poll_subscription_changes(last_check: str):
	"""
	Poll for subscription changes since last check

	Args:
		last_check: ISO 8601 timestamp of last check

	Returns:
		dict: Subscription changes if any
	"""
	try:
		# Authenticate user from token
		user = authenticate_from_token()

		if not user:
			frappe.throw(_("Unauthorized"), frappe.AuthenticationError)

		# Get current subscription
		current_status = get_subscription_status()

		if not current_status.get("success"):
			return current_status

		subscription = current_status.get("subscription")

		# Check if there are any changes since last check
		if subscription:
			last_check_dt = get_datetime(last_check)
			modified_dt = get_datetime(subscription.get("modified", now()))

			if modified_dt > last_check_dt:
				return {
					"success": True,
					"has_changes": True,
					"change_type": "updated",
					"subscription": subscription
				}

		return {
			"success": True,
			"has_changes": False,
			"current_status": subscription["status"] if subscription else "None"
		}

	except frappe.AuthenticationError:
		frappe.local.response["http_status_code"] = 401
		return {
			"success": False,
			"error": "Unauthorized"
		}
	except Exception as e:
		frappe.log_error(f"Poll subscription changes error: {str(e)}", "VS Code Auth Error")
		return {
			"success": False,
			"error": str(e)
		}


@frappe.whitelist(allow_guest=True)
def get_my_profile():
	"""
	Get authenticated user's profile information for VS Code settings

	Returns:
		dict: User profile with subscription details
	"""
	try:
		# Authenticate user from token
		user_email = authenticate_from_token()

		if not user_email:
			frappe.throw(_("Unauthorized"), frappe.AuthenticationError)

		# Get user details
		user = frappe.get_doc("User", user_email)

		# Get active subscription
		subscription_result = get_subscription_status()
		subscription = subscription_result.get("subscription") if subscription_result.get("success") else None

		# Get usage statistics (if available)
		usage_stats = get_user_usage_stats(user_email)

		return {
			"success": True,
			"profile": {
				"email": user.email,
				"full_name": user.full_name,
				"first_name": user.first_name,
				"last_name": user.last_name,
				"user_image": user.user_image or "",
				"mobile_no": user.mobile_no or "",
				"phone": user.phone or "",
				"bio": user.bio or "",
				"location": user.location or "",
				"created": str(user.creation),
				"enabled": user.enabled
			},
			"subscription": subscription,
			"usage": usage_stats
		}

	except frappe.AuthenticationError:
		frappe.local.response["http_status_code"] = 401
		return {
			"success": False,
			"error": "Unauthorized"
		}
	except Exception as e:
		frappe.log_error(f"Get profile error: {str(e)}", "VS Code Auth Error")
		return {
			"success": False,
			"error": str(e)
		}


def get_user_usage_stats(user_email: str) -> dict:
	"""
	Get user's usage statistics

	Args:
		user_email: User email

	Returns:
		dict: Usage statistics
	"""
	try:
		# Get usage logs for last 30 days
		from frappe.utils import add_days, today

		thirty_days_ago = add_days(today(), -30)

		usage_logs = frappe.get_all(
			"AI Usage Log",
			filters={
				"user": user_email,
				"timestamp": [">=", thirty_days_ago]
			},
			fields=["name"]
		)

		# Get today's usage
		today_usage = frappe.get_all(
			"AI Usage Log",
			filters={
				"user": user_email,
				"timestamp": [">=", today()]
			},
			fields=["name"]
		)

		return {
			"total_requests_30_days": len(usage_logs),
			"total_requests_today": len(today_usage),
			"last_used": str(frappe.db.get_value(
				"AI Usage Log",
				{"user": user_email},
				"timestamp",
				order_by="timestamp desc"
			)) if usage_logs else None
		}

	except Exception as e:
		frappe.log_error(f"Get usage stats error: {str(e)}", "Usage Stats Error")
		return {
			"total_requests_30_days": 0,
			"total_requests_today": 0,
			"last_used": None
		}


# Helper Functions

def generate_access_token(user: str) -> str:
	"""Generate secure access token for user"""
	token_data = f"{user}:{now()}:{secrets.token_hex(32)}"
	return hashlib.sha256(token_data.encode()).hexdigest()


def generate_refresh_token(user: str) -> str:
	"""Generate secure refresh token for user"""
	token_data = f"{user}:refresh:{now()}:{secrets.token_hex(32)}"
	return hashlib.sha256(token_data.encode()).hexdigest()


def get_token_from_header() -> str:
	"""Extract token from X-Access-Token or Authorization header"""
	# Try custom header first (doesn't trigger Frappe's auth validation)
	token = frappe.get_request_header("X-Access-Token")

	if token:
		return token

	# Fallback to Authorization header
	auth_header = frappe.get_request_header("Authorization")

	if auth_header and auth_header.startswith("Bearer "):
		return auth_header.replace("Bearer ", "")

	return None


def authenticate_from_token() -> str:
	"""Authenticate user from Bearer token"""
	access_token = get_token_from_header()

	if not access_token:
		return None

	# Use direct SQL query to bypass cache and get latest token
	result = frappe.db.sql("""
		SELECT user
		FROM `tabVS Code Auth Request`
		WHERE access_token = %s AND status = 'Completed'
		LIMIT 1
	""", (access_token,), as_dict=True)

	if not result:
		return None

	return result[0].user

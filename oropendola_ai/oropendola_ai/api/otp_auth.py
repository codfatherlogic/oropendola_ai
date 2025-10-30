# Copyright (c) 2025, sammish.thundiyil@gmail.com and contributors
# For license information, please see license.txt

"""
OTP-based Authentication API
Handles email OTP verification for signup and login
"""

import frappe
from frappe import _
import random
import hashlib
from datetime import datetime, timedelta


@frappe.whitelist(allow_guest=True)
def send_otp(email, purpose="signup", plan_id=None):
	"""
	Generate and send OTP to email address.
	
	Args:
		email (str): User's email address
		purpose (str): Purpose of OTP - 'signup', 'login', 'reset_password'
		plan_id (str): Selected plan ID (optional, for signup flow)
		
	Returns:
		dict: OTP sending result
	"""
	try:
		# Validate email format
		if not frappe.utils.validate_email_address(email):
			return {
				"success": False,
				"error": "Invalid email address"
			}
		
		# Check if user exists
		user_exists = frappe.db.exists("User", email)
		
		if purpose == "signup" and user_exists:
			return {
				"success": False,
				"error": "Email already registered. Please login instead.",
				"should_login": True
			}
		
		if purpose == "login" and not user_exists:
			return {
				"success": False,
				"error": "Email not found. Please signup first.",
				"should_signup": True
			}
		
		if purpose == "reset_password" and not user_exists:
			return {
				"success": False,
				"error": "Email not found. Please sign up first."
			}
		
		# Generate 6-digit OTP
		otp = str(random.randint(100000, 999999))
		
		# Hash OTP for storage
		otp_hash = hashlib.sha256(otp.encode()).hexdigest()
		
		# Store OTP in cache (valid for 30 minutes)
		cache_key = f"otp:{email}:{purpose}"
		frappe.cache().set_value(cache_key, {
			"otp_hash": otp_hash,
			"attempts": 0,
			"created_at": datetime.now().isoformat(),
			"plan_id": plan_id  # Store plan ID for signup flow
		}, expires_in_sec=1800)  # 30 minutes
		
		# Send OTP email
		subject = f"Your Oropendola AI Verification Code: {otp}"
		message = f"""
		<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; background: #0A0A0A; color: #fff; padding: 40px; border-radius: 10px;">
			<div style="text-align: center; margin-bottom: 30px;">
				<h1 style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-size: 32px; margin: 0;">
					Oropendola AI
				</h1>
			</div>
			
			<div style="background: #1A1A1A; padding: 30px; border-radius: 8px; margin-bottom: 30px;">
				<h2 style="color: #fff; margin-top: 0;">Your Verification Code</h2>
				<p style="color: #999; margin-bottom: 20px;">
					{"Welcome! " if purpose == "signup" else ""}Use this code to {"complete your registration" if purpose == "signup" else "login"}:
				</p>
				
				<div style="background: #2A2A2A; padding: 20px; border-radius: 6px; text-align: center; margin: 20px 0;">
					<span style="font-size: 36px; font-weight: bold; letter-spacing: 8px; color: #667eea;">
						{otp}
					</span>
				</div>
				
				<p style="color: #999; font-size: 14px; margin-top: 20px;">
					⏱️ This code expires in <strong style="color: #fff;">30 minutes</strong>
				</p>
			</div>
			
			<div style="background: #2A1A3A; border-left: 4px solid #667eea; padding: 15px; border-radius: 4px; margin-bottom: 30px;">
				<p style="color: #ddd; margin: 0; font-size: 14px;">
					🔒 <strong>Security Tip:</strong> Never share this code with anyone. Oropendola will never ask for your OTP via phone or social media.
				</p>
			</div>
			
			{f'<div style="background: #1A1A1A; padding: 20px; border-radius: 8px; margin-bottom: 20px;"><p style="color: #999; margin: 0; font-size: 14px;">📦 Selected Plan: <strong style="color: #fff;">{get_plan_name(plan_id)}</strong></p></div>' if plan_id else ''}
			
			<div style="text-align: center; padding-top: 20px; border-top: 1px solid #2A2A2A;">
				<p style="color: #666; font-size: 12px; margin: 5px 0;">
					If you didn't request this code, please ignore this email.
				</p>
				<p style="color: #666; font-size: 12px; margin: 5px 0;">
					Need help? Contact us at <a href="mailto:support@oropendola.ai" style="color: #667eea; text-decoration: none;">support@oropendola.ai</a>
				</p>
			</div>
		</div>
		"""
		
		frappe.sendmail(
			recipients=[email],
			subject=subject,
			message=message,
			sender="noreply@oropendola.ai",
			delayed=False,
			retry=3
		)
		
		frappe.logger().info(f"OTP sent to {email} for {purpose}")
		
		return {
			"success": True,
			"message": f"Verification code sent to {email}",
			"expires_in": 1800  # seconds
		}
		
	except Exception as e:
		frappe.log_error(f"Failed to send OTP: {str(e)}", "OTP Send Error")
		return {
			"success": False,
			"error": "Failed to send verification code. Please try again."
		}


def get_plan_name(plan_id):
	"""Get plan title from plan ID"""
	if not plan_id:
		return "None"
	
	plan = frappe.db.get_value("AI Plan", plan_id, "title")
	return plan or plan_id


@frappe.whitelist(allow_guest=True)
def verify_otp(email, otp, purpose="signup"):
	"""
	Verify OTP entered by user.
	
	Args:
		email (str): User's email address
		otp (str): OTP entered by user
		purpose (str): Purpose of OTP verification
		
	Returns:
		dict: Verification result
	"""
	try:
		# Get OTP from cache
		cache_key = f"otp:{email}:{purpose}"
		cached_data = frappe.cache().get_value(cache_key)
		
		if not cached_data:
			return {
				"success": False,
				"error": "OTP expired or not found. Please request a new code."
			}
		
		# Check attempts
		if cached_data.get("attempts", 0) >= 3:
			# Delete OTP after 3 failed attempts
			frappe.cache().delete_value(cache_key)
			return {
				"success": False,
				"error": "Too many failed attempts. Please request a new code.",
				"locked": True
			}
		
		# Hash entered OTP
		otp_hash = hashlib.sha256(otp.encode()).hexdigest()
		
		# Verify OTP
		if otp_hash != cached_data.get("otp_hash"):
			# Increment attempts
			cached_data["attempts"] = cached_data.get("attempts", 0) + 1
			frappe.cache().set_value(cache_key, cached_data, expires_in_sec=1800)
			
			remaining = 3 - cached_data["attempts"]
			return {
				"success": False,
				"error": f"Invalid code. {remaining} attempt{'s' if remaining != 1 else ''} remaining.",
				"remaining_attempts": remaining
			}
		
		# OTP verified successfully
		# Do NOT delete OTP here - let signup_with_otp delete it
		# This allows verification to succeed without deleting the OTP prematurely
		
		frappe.logger().info(f"OTP verified successfully for {email}")
		
		return {
			"success": True,
			"message": "Verification successful!",
			"email": email,
			"plan_id": cached_data.get("plan_id")
		}
		
	except Exception as e:
		frappe.log_error(f"Failed to verify OTP: {str(e)}", "OTP Verify Error")
		return {
			"success": False,
			"error": "Verification failed. Please try again."
		}


@frappe.whitelist(allow_guest=True)
def resend_otp(email, purpose="signup", plan_id=None):
	"""
	Resend OTP to email address.
	
	Args:
		email (str): User's email address
		purpose (str): Purpose of OTP
		plan_id (str): Selected plan ID (optional)
		
	Returns:
		dict: Result
	"""
	try:
		# Check if previous OTP exists
		cache_key = f"otp:{email}:{purpose}"
		cached_data = frappe.cache().get_value(cache_key)
		
		if cached_data:
			# Check if enough time has passed (30 seconds cooldown)
			created_at = datetime.fromisoformat(cached_data.get("created_at"))
			time_diff = (datetime.now() - created_at).total_seconds()
			
			if time_diff < 30:
				wait_time = int(30 - time_diff)
				return {
					"success": False,
					"error": f"Please wait {wait_time} seconds before requesting a new code.",
					"wait_seconds": wait_time
				}
		
		# Send new OTP
		return send_otp(email, purpose, plan_id)
		
	except Exception as e:
		frappe.log_error(f"Failed to resend OTP: {str(e)}", "OTP Resend Error")
		return {
			"success": False,
			"error": "Failed to resend code. Please try again."
		}


@frappe.whitelist(allow_guest=True)
def signup_with_otp(email, full_name, password, otp, plan_id=None):
	"""
	Complete signup after OTP verification.
	Creates User, AI Customer, and optionally AI Subscription.
	
	Args:
		email (str): User's email address
		full_name (str): User's full name
		password (str): User's password
		otp (str): OTP for verification
		plan_id (str): Selected plan ID (optional)
		
	Returns:
		dict: Signup result
	"""
	try:
		# Verify OTP first
		otp_result = verify_otp(email, otp, "signup")
		
		if not otp_result.get("success"):
			return otp_result
		
		# OTP verified - now proceed with account creation
		# Delete OTP after successful verification (single use)
		cache_key = f"otp:{email}:signup"
		frappe.cache().delete_value(cache_key)
		
		# Check if user already exists (double check)
		if frappe.db.exists("User", email):
			return {
				"success": False,
				"error": "Email already registered. Please login instead."
			}
		
		# Create Frappe User
		user = frappe.get_doc({
			"doctype": "User",
			"email": email,
			"first_name": full_name.split()[0] if full_name else email.split("@")[0],
			"last_name": " ".join(full_name.split()[1:]) if len(full_name.split()) > 1 else "",
			"enabled": 1,
			"new_password": password,
			"user_type": "Website User",
			"send_welcome_email": 0  # We'll send custom email
		})
		user.flags.ignore_permissions = True
		user.flags.ignore_password_policy = False
		user.insert()
		
		# Create AI Customer
		customer = frappe.get_doc({
			"doctype": "AI Customer",
			"customer_name": full_name,
			"email": email,
			"user": email,
			"email_verified": 1,  # OTP verified = email verified
			"status": "Active"
		})
		customer.flags.ignore_permissions = True
		customer.insert()
		
		# If plan selected, create subscription
		subscription_id = None
		if plan_id:
			subscription_result = create_subscription_for_customer(email, plan_id)
			if subscription_result.get("success"):
				subscription_id = subscription_result.get("subscription_id")
		
		frappe.db.commit()
		
		# Send welcome email
		send_welcome_email(email, full_name)
		
		frappe.logger().info(f"User created successfully: {email}")
		
		return {
			"success": True,
			"message": "Account created successfully!",
			"user_id": email,
			"customer_id": customer.name,
			"subscription_id": subscription_id,
			"plan_id": plan_id
		}
		
	except Exception as e:
		frappe.db.rollback()
		error_msg = str(e)
		frappe.log_error(f"Signup failed: {error_msg}", "Signup Error")
		return {
			"success": False,
			"error": error_msg  # Return actual error, not generic message
		}


def create_subscription_for_customer(email, plan_id):
	"""Create subscription for customer"""
	try:
		# Get customer
		customer = frappe.get_doc("AI Customer", {"email": email})
		
		# Get plan
		plan = frappe.get_doc("AI Plan", plan_id)
		
		# Create subscription
		subscription = frappe.get_doc({
			"doctype": "AI Subscription",
			"user": email,
			"customer": customer.name,
			"plan": plan.name,
			"status": "Pending",  # Will be Active after payment
			"start_date": frappe.utils.nowdate(),
			"end_date": frappe.utils.add_days(frappe.utils.nowdate(), plan.duration_days),
			"daily_quota_limit": plan.requests_limit_per_day,
			"daily_quota_remaining": plan.requests_limit_per_day,
			"monthly_budget_limit": plan.monthly_budget_limit or 0,
			"monthly_budget_used": 0,
			"auto_renew": 1
		})
		subscription.flags.ignore_permissions = True
		subscription.insert()
		
		return {
			"success": True,
			"subscription_id": subscription.name
		}
		
	except Exception as e:
		frappe.log_error(f"Failed to create subscription: {str(e)}", "Subscription Error")
		return {
			"success": False,
			"error": str(e)
		}


def send_welcome_email(email, full_name):
	"""Send welcome email to new user"""
	try:
		subject = "Welcome to Oropendola AI! 🎉"
		message = f"""
		<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; background: #0A0A0A; color: #fff; padding: 40px; border-radius: 10px;">
			<div style="text-align: center; margin-bottom: 30px;">
				<h1 style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-size: 32px; margin: 0;">
					Welcome to Oropendola AI!
				</h1>
			</div>
			
			<div style="background: #1A1A1A; padding: 30px; border-radius: 8px; margin-bottom: 30px;">
				<h2 style="color: #fff; margin-top: 0;">Hi {full_name}! 👋</h2>
				<p style="color: #999; line-height: 1.6;">
					Your account has been successfully created. You're now part of the Oropendola AI community!
				</p>
				
				<div style="margin: 30px 0;">
					<h3 style="color: #667eea; font-size: 18px;">What's Next?</h3>
					<ul style="color: #999; line-height: 1.8;">
						<li>🚀 Complete your subscription payment</li>
						<li>🔑 Get your API key from the dashboard</li>
						<li>💻 Install our VS Code extension</li>
						<li>🤖 Start coding with AI assistance</li>
					</ul>
				</div>
				
				<div style="text-align: center; margin: 30px 0;">
					<a href="https://oropendola.ai/my-profile" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: #fff; padding: 15px 40px; text-decoration: none; border-radius: 6px; display: inline-block; font-weight: bold;">
						Go to Dashboard
					</a>
				</div>
			</div>
			
			<div style="background: #2A1A3A; border-left: 4px solid #667eea; padding: 15px; border-radius: 4px; margin-bottom: 30px;">
				<p style="color: #ddd; margin: 0; font-size: 14px;">
					📚 <strong>Need Help?</strong> Check out our <a href="https://oropendola.ai/docs" style="color: #667eea; text-decoration: none;">documentation</a> or contact support.
				</p>
			</div>
			
			<div style="text-align: center; padding-top: 20px; border-top: 1px solid #2A2A2A;">
				<p style="color: #666; font-size: 12px; margin: 5px 0;">
					Questions? Contact us at <a href="mailto:support@oropendola.ai" style="color: #667eea; text-decoration: none;">support@oropendola.ai</a>
				</p>
			</div>
		</div>
		"""
		
		frappe.sendmail(
			recipients=[email],
			subject=subject,
			message=message,
			sender="noreply@oropendola.ai",
			delayed=False
		)
		
	except Exception as e:
		frappe.log_error(f"Failed to send welcome email: {str(e)}", "Welcome Email Error")


@frappe.whitelist(allow_guest=True)
def login_with_otp(email, otp):
	"""
	Login using OTP instead of password.
	
	Args:
		email (str): User's email address
		otp (str): OTP for verification
		
	Returns:
		dict: Login result
	"""
	try:
		# Verify OTP
		otp_result = verify_otp(email, otp, "login")
		
		if not otp_result.get("success"):
			return otp_result
		
		# Check if user exists
		if not frappe.db.exists("User", email):
			return {
				"success": False,
				"error": "User not found"
			}
		
		# Login user
		frappe.local.login_manager.login_as(email)
		frappe.local.login_manager.user = email
		frappe.local.login_manager.post_login()
		
		frappe.logger().info(f"User logged in via OTP: {email}")
		
		return {
			"success": True,
			"message": "Login successful!",
			"user_id": email,
			"redirect": "/my-profile"
		}
		
	except Exception as e:
		frappe.log_error(f"OTP login failed: {str(e)}", "OTP Login Error")
		return {
			"success": False,
			"error": "Login failed. Please try again."
		}


@frappe.whitelist(allow_guest=True)
def reset_password_with_otp(email, password):
	"""
	Reset user password after OTP verification.
	
	Args:
		email (str): User's email address
		password (str): New password
		
	Returns:
		dict: Reset result
	"""
	try:
		# Check if user exists
		if not frappe.db.exists("User", email):
			return {
				"success": False,
				"error": "Email not found. Please sign up first."
			}
		
		# Update password using Frappe's update_password method
		from frappe.utils.password import update_password
		update_password(user=email, pwd=password, logout_all_sessions=1)
		
		frappe.db.commit()
		
		# Delete OTP after successful password reset
		cache_key = f"otp:{email}:reset_password"
		frappe.cache().delete_value(cache_key)
		
		frappe.logger().info(f"Password reset successfully for {email}")
		
		return {
			"success": True,
			"message": "Password reset successfully!"
		}
		
	except Exception as e:
		frappe.db.rollback()
		error_msg = str(e)
		frappe.log_error(f"Password reset failed: {error_msg}", "Password Reset Error")
		return {
			"success": False,
			"error": error_msg
		}

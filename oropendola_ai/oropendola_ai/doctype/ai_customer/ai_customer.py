# Copyright (c) 2025, sammish.thundiyil@gmail.com and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import now, add_days
import secrets
import hashlib


class AICustomer(Document):
	"""
	AI Customer DocType for managing customer accounts.
	Links customers with Frappe User accounts and handles email verification.
	"""
	
	def before_insert(self):
		"""Initialize customer before insert"""
		if not self.status:
			self.status = "Pending Verification"
		
		if not self.email_verified:
			self.email_verified = 0
	
	def after_insert(self):
		"""Send verification email after customer creation"""
		if not self.email_verified:
			self.send_verification_email()
	
	def validate(self):
		"""Validate customer data"""
		# Ensure email is unique
		if self.has_value_changed("email"):
			existing = frappe.db.exists("AI Customer", {"email": self.email, "name": ["!=", self.name]})
			if existing:
				frappe.throw(f"Email {self.email} already registered")
		
		# Update status based on verification
		if self.email_verified and self.status == "Pending Verification":
			self.status = "Active"
	
	def send_verification_email(self):
		"""
		Generate verification token and send email.
		"""
		try:
			# Generate verification token
			token = secrets.token_urlsafe(32)
			token_hash = hashlib.sha256(token.encode()).hexdigest()
			
			# Store hashed token
			self.db_set("verification_token", token_hash, update_modified=False)
			self.db_set("verification_sent_at", now(), update_modified=False)
			frappe.db.commit()
			
			# Build verification link
			verification_url = f"{frappe.utils.get_url()}/api/method/oropendola_ai.oropendola_ai.api.auth.verify_email?token={token}"
			
			# Send email
			frappe.sendmail(
				recipients=[self.email],
				subject="Verify Your Oropendola AI Account",
				message=f"""
					<h2>Welcome to Oropendola AI!</h2>
					<p>Hello {self.customer_name},</p>
					<p>Thank you for signing up. Please verify your email address by clicking the link below:</p>
					<p><a href="{verification_url}" style="background-color: #4CAF50; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Verify Email</a></p>
					<p>Or copy this link: {verification_url}</p>
					<p>This link will expire in 24 hours.</p>
					<p>If you didn't create this account, please ignore this email.</p>
					<p>Best regards,<br>Oropendola AI Team</p>
				"""
			)
			
			frappe.msgprint(f"Verification email sent to {self.email}")
			
		except Exception as e:
			frappe.log_error(f"Failed to send verification email: {str(e)}", "Email Verification Error")
			frappe.throw("Failed to send verification email. Please contact support.")
	
	def verify_email(self, token):
		"""
		Verify email using token.
		
		Args:
			token (str): Verification token from email
			
		Returns:
			bool: True if verified successfully
		"""
		# Check if already verified
		if self.email_verified:
			return True
		
		# Hash provided token
		token_hash = hashlib.sha256(token.encode()).hexdigest()
		
		# Verify token matches
		if token_hash != self.verification_token:
			return False
		
		# Check token expiry (24 hours)
		if self.verification_sent_at:
			from frappe.utils import get_datetime
			expiry_time = add_days(get_datetime(self.verification_sent_at), 1)
			if get_datetime(now()) > expiry_time:
				return False  # Token expired
		
		# Mark as verified
		self.db_set("email_verified", 1, update_modified=False)
		self.db_set("verified_at", now(), update_modified=False)
		self.db_set("status", "Active", update_modified=False)
		frappe.db.commit()
		
		# Create Frappe User if not exists
		if not self.user:
			self.create_frappe_user()
		
		return True
	
	def create_frappe_user(self):
		"""
		Create linked Frappe User account after verification.
		"""
		try:
			# Check if user already exists
			if frappe.db.exists("User", self.email):
				user = frappe.get_doc("User", self.email)
			else:
				# Create new user
				user = frappe.get_doc({
					"doctype": "User",
					"email": self.email,
					"first_name": self.customer_name,
					"send_welcome_email": 0,
					"enabled": 1,
					"user_type": "Website User"
				})
				user.insert(ignore_permissions=True)
			
			# Link user to customer
			self.db_set("user", user.name, update_modified=False)
			frappe.db.commit()
			
			frappe.log_error(f"Frappe User created for customer {self.name}", "User Creation")
			
		except Exception as e:
			frappe.log_error(f"Failed to create Frappe User: {str(e)}", "User Creation Error")
	
	def get_or_create_subscription(self, plan_id):
		"""
		Get existing active subscription or create new one.
		
		Args:
			plan_id (str): AI Plan ID
			
		Returns:
			dict: Subscription details
		"""
		# Check for existing active subscription
		existing = frappe.get_all(
			"AI Subscription",
			filters={
				"customer": self.name,
				"status": ["in", ["Active", "Trial"]]
			},
			fields=["name", "plan", "status"],
			limit=1
		)
		
		if existing:
			return frappe.get_doc("AI Subscription", existing[0].name)
		
		# Create new subscription
		subscription = frappe.get_doc({
			"doctype": "AI Subscription",
			"customer": self.name,
			"plan": plan_id,
			"status": "Active",
			"billing_email": self.email
		})
		subscription.insert(ignore_permissions=True)
		frappe.db.commit()
		
		return subscription

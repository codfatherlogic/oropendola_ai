# Copyright (c) 2025, sammish.thundiyil@gmail.com and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import today, add_days, nowdate, getdate
import secrets
import hashlib


class AISubscription(Document):
	"""
	AI Subscription DocType for managing customer subscriptions.
	Handles subscription lifecycle, quota management, and API key generation.
	"""
	
	def before_insert(self):
		"""Initialize subscription before insert"""
		self.set_dates()
		self.set_quota()
		self.initialize_monthly_budget()
		self.created_by_user = frappe.session.user
	
	def after_insert(self):
		"""Create API key after subscription is created"""
		self.create_api_key()
	
	def validate(self):
		"""Validate subscription data"""
		self.validate_dates()
		self.validate_status()
		self.update_quota_from_plan()
	
	def set_dates(self):
		"""Set subscription start and end dates"""
		if not self.start_date:
			self.start_date = today()
		
		if not self.end_date:
			plan = frappe.get_doc("AI Plan", self.plan)
			if plan.duration_days and plan.duration_days > 0:
				self.end_date = add_days(self.start_date, plan.duration_days)
				
			if plan.is_trial:
				self.status = "Trial"
				self.trial_end_date = self.end_date
	
	def set_quota(self):
		"""Initialize daily quota - only give quota if subscription is Active or Trial"""
		plan = frappe.get_doc("AI Plan", self.plan)
		self.daily_quota_limit = plan.requests_limit_per_day or 0

		# Only give quota if subscription is Active, Trial, or if it's a free plan
		is_free_plan = (plan.price or 0) == 0 and (plan.is_free or False)
		if self.status in ["Active", "Trial"] or is_free_plan:
			quota_limit = plan.requests_limit_per_day or 0
			self.daily_quota_remaining = quota_limit if quota_limit > 0 else -1
		else:
			# Pending subscriptions get 0 quota until payment is completed
			self.daily_quota_remaining = 0
			frappe.logger().info(f"Subscription {self.name} is {self.status} - quota set to 0")

		self.priority_score = plan.priority_score or 0
	
	def validate_dates(self):
		"""Validate subscription dates"""
		if self.end_date and getdate(self.start_date) > getdate(self.end_date):
			frappe.throw("Start date cannot be after end date")
	
	def validate_status(self):
		"""Check if subscription has expired"""
		if self.end_date and getdate(self.end_date) < getdate(today()) and self.status == "Active":
			self.status = "Expired"
	
	def update_quota_from_plan(self):
		"""Update quota limits from plan if changed"""
		if self.has_value_changed("plan"):
			plan = frappe.get_doc("AI Plan", self.plan)
			self.daily_quota_limit = plan.requests_limit_per_day or 0
			self.priority_score = plan.priority_score or 0
	
	def create_api_key(self):
		"""Generate and create API key for this subscription - only for Active/Trial subscriptions"""
		# Check if we should create API key based on subscription status
		plan = frappe.get_doc("AI Plan", self.plan)

		# Only create API key if subscription is Active, Trial, or it's a free plan
		is_free_plan = (plan.price or 0) == 0 and (plan.is_free or False)
		if self.status not in ["Active", "Trial"] and not is_free_plan:
			frappe.logger().info(f"Skipping API key creation for {self.status} subscription {self.name} - will create after payment")
			return

		try:
			# Generate secure API key
			raw_key = secrets.token_urlsafe(32)
			key_hash = hashlib.sha256(raw_key.encode()).hexdigest()

			# Create AI API Key document
			api_key_doc = frappe.get_doc({
				"doctype": "AI API Key",
				"user": self.user,  # Changed from customer to user
				"subscription": self.name,
				"key_hash": key_hash,
				"key_prefix": raw_key[:8],
				"status": "Active",
				"created_by": frappe.session.user
			})
			api_key_doc.insert(ignore_permissions=True)

			# Link API key to subscription
			self.db_set("api_key_link", api_key_doc.name)

			# Store raw key in cache temporarily (5 minutes) for user to retrieve
			cache_key = f"api_key_raw:{self.name}"
			frappe.cache().set_value(cache_key, raw_key, expires_in_sec=300)

			frappe.msgprint(f"API Key generated successfully. Retrieve it immediately as it won't be shown again.")

		except Exception as e:
			frappe.log_error(f"Failed to create API key for subscription {self.name}: {str(e)}")
			frappe.throw("Failed to generate API key. Please contact support.")
	
	def reset_daily_quota(self):
		"""Reset daily quota (called by scheduler)"""
		if self.status == "Active" and self.daily_quota_limit != -1:
			self.db_set("daily_quota_remaining", self.daily_quota_limit)
			frappe.db.commit()
	
	def consume_quota(self, units=1):
		"""Consume quota units"""
		if self.daily_quota_limit == -1:
			# Unlimited plan
			return True
		
		if self.daily_quota_remaining >= units:
			self.db_set("daily_quota_remaining", self.daily_quota_remaining - units, update_modified=False)
			self.db_set("total_usage", (self.total_usage or 0) + units, update_modified=False)
			self.db_set("total_requests", (self.total_requests or 0) + 1, update_modified=False)
			frappe.db.commit()
			return True
		
		return False
	
	def is_active(self):
		"""Check if subscription is currently active"""
		return self.status in ["Active", "Trial"]
	
	def is_expired(self):
		"""Check if subscription has expired"""
		if self.end_date:
			return getdate(self.end_date) < getdate(today())
		return False
	
	def cancel_subscription(self, reason=None):
		"""Cancel the subscription"""
		self.status = "Cancelled"
		self.cancelled_at = frappe.utils.now()
		if reason:
			self.cancellation_reason = reason

		# Revoke API key
		if self.api_key_link:
			api_key = frappe.get_doc("AI API Key", self.api_key_link)
			api_key.status = "Revoked"
			api_key.save(ignore_permissions=True)

		self.save(ignore_permissions=True)

	def activate_after_payment(self):
		"""
		Activate subscription after successful payment.
		This method is called when payment is confirmed successful.
		"""
		frappe.logger().info(f"Activating subscription {self.name} after payment")

		# Set status to Active
		self.status = "Active"

		# Set quota (will now give full quota since status is Active)
		self.set_quota()

		# Create API key (will now create since status is Active)
		if not self.api_key_link:
			self.create_api_key()

		# Update last payment date
		self.last_payment_date = today()

		# Save the changes
		self.save(ignore_permissions=True)
		frappe.db.commit()

		frappe.logger().info(f"Subscription {self.name} activated successfully - Status: {self.status}, Quota: {self.daily_quota_remaining}, API Key: {self.api_key_link}")

		return True

	def get_plan_details(self):
		"""Get plan configuration"""
		return frappe.get_doc("AI Plan", self.plan)
	
	@frappe.whitelist()
	def get_raw_api_key(self):
		"""Retrieve raw API key from cache (one-time only)"""
		cache_key = f"api_key_raw:{self.name}"
		raw_key = frappe.cache().get_value(cache_key)
		
		if raw_key:
			# Delete from cache after retrieval
			frappe.cache().delete_value(cache_key)
			return raw_key
		
		return None
	
	# ========================================
	# User-Based Monthly Budget Tracking
	# ========================================
	
	def initialize_monthly_budget(self):
		"""Initialize monthly budget tracking for new subscription"""
		import datetime
		
		# Set current month start (first day of current month)
		today_date = datetime.date.today()
		self.current_month_start = today_date.replace(day=1)
		
		# Initialize budget used to 0
		self.monthly_budget_used = 0.0
		
		# Set alert threshold if not already set
		if not self.budget_alert_threshold:
			self.budget_alert_threshold = 0.9  # 90%
	
	def check_monthly_budget(self, estimated_cost: float) -> tuple:
		"""
		Check if user has sufficient monthly budget remaining.
		Returns: (allowed: bool, message: str, remaining: float)
		"""
		import datetime
		
		# Check if we need to reset monthly budget (new month)
		self.reset_monthly_budget_if_needed()
		
		# Get monthly budget limit from plan
		if not self.monthly_budget_limit or self.monthly_budget_limit == 0:
			# No budget limit (unlimited)
			return (True, "Unlimited budget", -1)
		
		current_used = self.monthly_budget_used or 0
		remaining = self.monthly_budget_limit - current_used
		
		# Check if estimated cost exceeds remaining budget
		if estimated_cost > remaining:
			return (
				False,
				f"Insufficient budget. Required: {estimated_cost:.2f}, Remaining: {remaining:.2f}",
				remaining
			)
		
		# Check if approaching alert threshold
		threshold = self.budget_alert_threshold or 0.9
		alert_amount = self.monthly_budget_limit * threshold
		
		if current_used + estimated_cost >= alert_amount:
			self.send_budget_alert(current_used + estimated_cost, remaining - estimated_cost)
		
		return (True, f"Budget check passed. Remaining: {remaining - estimated_cost:.2f}", remaining)
	
	def consume_monthly_budget(self, cost: float):
		"""Consume monthly budget for this user"""
		# Reset if new month
		self.reset_monthly_budget_if_needed()
		
		# Increment budget used
		current_used = self.monthly_budget_used or 0
		new_used = current_used + cost
		
		self.db_set("monthly_budget_used", new_used, update_modified=False)
		frappe.db.commit()
		
		return new_used
	
	def reset_monthly_budget_if_needed(self):
		"""Reset monthly budget if a new month has started"""
		import datetime
		
		today_date = datetime.date.today()
		first_of_month = today_date.replace(day=1)
		
		if not self.current_month_start or getdate(self.current_month_start) < first_of_month:
			# New month - reset budget
			self.db_set("current_month_start", first_of_month, update_modified=False)
			self.db_set("monthly_budget_used", 0.0, update_modified=False)
			frappe.db.commit()
			
			frappe.log_error(
				f"Monthly budget reset for user {self.customer} (subscription: {self.name})",
				"Budget Reset"
			)
	
	def send_budget_alert(self, current_usage: float, remaining: float):
		"""Send alert when budget threshold is reached"""
		try:
			threshold_pct = int((self.budget_alert_threshold or 0.9) * 100)
			usage_pct = int((current_usage / self.monthly_budget_limit) * 100)
			
			# Check if alert already sent this month
			alert_key = f"budget_alert:{self.name}:{self.current_month_start}"
			if frappe.cache().get_value(alert_key):
				return  # Alert already sent
			
			# Send email alert
			frappe.sendmail(
				recipients=[self.billing_email or self.user],  # Changed from getting customer email
				subject=f"Budget Alert: {usage_pct}% Used - Oropendola AI",
				message=f"""
					<p>Hello,</p>
					<p>Your Oropendola AI monthly budget has reached <strong>{threshold_pct}%</strong> of your limit.</p>
					<ul>
						<li>Budget Limit: {self.monthly_budget_limit:.2f}</li>
						<li>Current Usage: {current_usage:.2f} ({usage_pct}%)</li>
						<li>Remaining: {remaining:.2f}</li>
					</ul>
					<p>To avoid service interruption, please consider upgrading your plan or managing your usage.</p>
					<p>Thank you,<br>Oropendola AI Team</p>
				"""
			)
			
			# Cache alert to avoid duplicate sends
			frappe.cache().set_value(alert_key, True, expires_in_sec=86400)  # 24 hours
			
		except Exception as e:
			frappe.log_error(f"Failed to send budget alert: {str(e)}", "Budget Alert Error")
	
	def get_monthly_budget_stats(self) -> dict:
		"""Get monthly budget statistics for this user"""
		self.reset_monthly_budget_if_needed()
		
		limit = self.monthly_budget_limit or 0
		used = self.monthly_budget_used or 0
		remaining = limit - used if limit > 0 else -1
		usage_pct = (used / limit * 100) if limit > 0 else 0
		
		return {
			"monthly_budget_limit": limit,
			"monthly_budget_used": used,
			"monthly_budget_remaining": remaining,
			"usage_percentage": round(usage_pct, 2),
			"current_month_start": str(self.current_month_start),
			"alert_threshold": self.budget_alert_threshold or 0.9,
			"unlimited": limit == 0 or remaining == -1
		}

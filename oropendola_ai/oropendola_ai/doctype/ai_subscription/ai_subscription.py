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
			if plan.duration_days > 0:
				self.end_date = add_days(self.start_date, plan.duration_days)
				
			if plan.is_trial:
				self.status = "Trial"
				self.trial_end_date = self.end_date
	
	def set_quota(self):
		"""Initialize daily quota"""
		plan = frappe.get_doc("AI Plan", self.plan)
		self.daily_quota_limit = plan.requests_limit_per_day
		self.daily_quota_remaining = plan.requests_limit_per_day if plan.requests_limit_per_day > 0 else -1
		self.priority_score = plan.priority_score
	
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
			self.daily_quota_limit = plan.requests_limit_per_day
			self.priority_score = plan.priority_score
	
	def create_api_key(self):
		"""Generate and create API key for this subscription"""
		try:
			# Generate secure API key
			raw_key = secrets.token_urlsafe(32)
			key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
			
			# Create AI API Key document
			api_key_doc = frappe.get_doc({
				"doctype": "AI API Key",
				"customer": self.customer,
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

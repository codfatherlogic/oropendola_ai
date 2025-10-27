# Copyright (c) 2025, sammish.thundiyil@gmail.com and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
import hashlib


class AIAPIKey(Document):
	"""
	AI API Key DocType for managing API keys.
	Handles key validation, usage tracking, and revocation.
	"""
	
	def validate(self):
		"""Validate API key"""
		self.validate_key_hash()
		self.validate_subscription()
	
	def validate_key_hash(self):
		"""Ensure key hash is provided"""
		if not self.key_hash:
			frappe.throw("Key hash is required")
	
	def validate_subscription(self):
		"""Check subscription status"""
		if self.subscription:
			subscription = frappe.get_doc("AI Subscription", self.subscription)
			if subscription.status in ["Expired", "Cancelled"]:
				self.status = "Revoked"
				self.revoke_reason = f"Subscription is {subscription.status}"
	
	def update_usage(self, success=True):
		"""Update usage statistics"""
		self.db_set("last_used", frappe.utils.now(), update_modified=False)
		self.db_set("usage_count", (self.usage_count or 0) + 1, update_modified=False)
		self.db_set("total_requests", (self.total_requests or 0) + 1, update_modified=False)
		
		if not success:
			self.db_set("failed_requests", (self.failed_requests or 0) + 1, update_modified=False)
		
		frappe.db.commit()
	
	def revoke(self, reason=None):
		"""Revoke the API key"""
		self.status = "Revoked"
		self.revoked_at = frappe.utils.now()
		self.revoked_by = frappe.session.user
		if reason:
			self.revoke_reason = reason
		self.save(ignore_permissions=True)
	
	def is_valid(self):
		"""Check if key is currently valid"""
		if self.status != "Active":
			return False
		
		# Check subscription status
		if self.subscription:
			subscription = frappe.get_doc("AI Subscription", self.subscription)
			return subscription.is_active()
		
		return False
	
	@staticmethod
	def verify_key(raw_key):
		"""Verify a raw API key and return the API Key document if valid"""
		key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
		
		# Find API key by hash
		api_keys = frappe.get_all(
			"AI API Key",
			filters={"key_hash": key_hash, "status": "Active"},
			fields=["name", "customer", "subscription", "status"]
		)
		
		if not api_keys:
			return None
		
		api_key_doc = frappe.get_doc("AI API Key", api_keys[0].name)
		
		# Check if valid
		if api_key_doc.is_valid():
			return api_key_doc
		
		return None
	
	@staticmethod
	def get_subscription_from_key(raw_key):
		"""Get subscription details from API key"""
		api_key = AIAPIKey.verify_key(raw_key)
		
		if api_key and api_key.subscription:
			return frappe.get_doc("AI Subscription", api_key.subscription)
		
		return None

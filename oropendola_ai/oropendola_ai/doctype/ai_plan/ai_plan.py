# Copyright (c) 2025, sammish.thundiyil@gmail.com and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class AIPlan(Document):
	"""
	AI Plan DocType for managing subscription plans.
	Defines pricing, quotas, features, and model access for customers.
	"""
	
	def validate(self):
		"""Validate plan configuration"""
		self.validate_pricing()
		self.validate_quotas()
		self.validate_priority()
	
	def validate_pricing(self):
		"""Ensure price is positive"""
		if self.price is not None and self.price < 0:
			frappe.throw("Price cannot be negative")

		if self.duration_days is not None and self.duration_days < 0:
			frappe.throw("Duration cannot be negative")
	
	def validate_quotas(self):
		"""Validate quota limits"""
		if self.requests_limit_per_day is not None and self.requests_limit_per_day < -1:
			frappe.throw("Requests limit must be -1 (unlimited) or positive integer")

		if self.rate_limit_qps is not None and self.rate_limit_qps < 0:
			frappe.throw("Rate limit must be 0 (no limit) or positive integer")
	
	def validate_priority(self):
		"""Ensure priority score is reasonable"""
		if self.priority_score is not None and self.priority_score < 0:
			frappe.throw("Priority score cannot be negative")

		if self.priority_score is not None and self.priority_score > 100:
			frappe.throw("Priority score cannot exceed 100")
	
	def get_daily_quota(self):
		"""Get daily request quota"""
		return self.requests_limit_per_day if self.requests_limit_per_day != -1 else None
	
	def is_unlimited(self):
		"""Check if plan has unlimited requests"""
		return self.requests_limit_per_day == -1
	
	def has_feature(self, feature_name):
		"""Check if plan has a specific feature"""
		for feature in self.features:
			if feature.feature_name == feature_name and feature.enabled:
				return True
		return False
	
	def get_allowed_models(self):
		"""Get list of allowed model names"""
		return [model.model_name for model in self.model_access if model.is_allowed]
	
	def get_model_cost_weight(self, model_name):
		"""
		Get cost weight for a specific model in this plan.
		Cost weight influences routing decisions - higher weight = more likely to be selected.
		
		Args:
			model_name (str): Name of the model
			
		Returns:
			float: Cost weight (default: 10 if not found)
		"""
		for model in self.model_access:
			if model.model_name == model_name and model.is_allowed:
				return float(model.cost_weight or 10)
		return 10  # Default weight
	
	def get_smart_routing_config(self):
		"""
		Get smart routing configuration for this plan.
		
		Returns:
			dict: Smart routing configuration
		"""
		return {
			"default_mode": self.default_routing_mode or "auto",
			"enable_session_continuity": bool(self.enable_session_continuity),
			"session_ttl": self.session_ttl or 3600,
			"enable_task_complexity_detection": bool(self.enable_task_complexity_detection),
			"correlation_threshold": self.correlation_threshold or 0.7,
			"monthly_budget_limit": self.monthly_budget_limit or 0
		}

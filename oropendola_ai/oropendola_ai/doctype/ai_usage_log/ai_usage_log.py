# Copyright (c) 2025, sammish.thundiyil@gmail.com and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
import uuid


class AIUsageLog(Document):
	"""
	AI Usage Log DocType for tracking AI model requests.
	Used for billing, analytics, and auditing.
	"""
	
	def before_insert(self):
		"""Set defaults before insert"""
		if not self.request_id:
			self.request_id = str(uuid.uuid4())
		
		if not self.timestamp:
			self.timestamp = frappe.utils.now()
	
	def validate(self):
		"""Validate usage log"""
		self.validate_cost_units()
	
	def validate_cost_units(self):
		"""Ensure cost units is positive"""
		if self.request_cost_units < 0:
			frappe.throw("Request cost units cannot be negative")
	
	@staticmethod
	def log_request(subscription, model, cost_units, status, latency_ms=None, 
	                error_message=None, tokens_input=None, tokens_output=None,
	                ip_address=None, user_agent=None, priority_score=None,
	                queue_time_ms=None, endpoint=None):
		"""
		Helper method to log an API request.
		Can be called from routing service.
		"""
		try:
			# Get subscription details
			subscription_doc = frappe.get_doc("AI Subscription", subscription)
			
			# Mask API key (show only first 8 chars)
			api_key_masked = "****"
			if subscription_doc.api_key_link:
				api_key_doc = frappe.get_doc("AI API Key", subscription_doc.api_key_link)
				api_key_masked = api_key_doc.key_prefix + "****"
			
			# Create log entry
			log_doc = frappe.get_doc({
				"doctype": "AI Usage Log",
				"timestamp": frappe.utils.now(),
				"request_id": str(uuid.uuid4()),
				"customer": subscription_doc.customer,
				"subscription": subscription,
				"api_key": api_key_masked,
				"model": model,
				"endpoint": endpoint,
				"request_cost_units": cost_units,
				"tokens_input": tokens_input,
				"tokens_output": tokens_output,
				"status": status,
				"latency_ms": latency_ms,
				"error_message": error_message,
				"ip_address": ip_address,
				"user_agent": user_agent,
				"priority_score": priority_score or subscription_doc.priority_score,
				"queue_time_ms": queue_time_ms
			})
			
			log_doc.insert(ignore_permissions=True)
			frappe.db.commit()
			
			return log_doc.name
			
		except Exception as e:
			frappe.log_error(f"Failed to log usage: {str(e)}", "AI Usage Log Error")
			return None
	
	@staticmethod
	def get_usage_summary(customer, start_date=None, end_date=None):
		"""Get usage summary for a customer"""
		filters = {"customer": customer}
		
		if start_date:
			filters["timestamp"] = [">=", start_date]
		if end_date:
			filters["timestamp"] = ["<=", end_date]
		
		logs = frappe.get_all(
			"AI Usage Log",
			filters=filters,
			fields=["model", "status", "request_cost_units", "latency_ms"]
		)
		
		summary = {
			"total_requests": len(logs),
			"total_cost_units": sum(log.request_cost_units for log in logs),
			"successful_requests": len([log for log in logs if log.status == "Success"]),
			"failed_requests": len([log for log in logs if log.status != "Success"]),
			"avg_latency_ms": sum(log.latency_ms or 0 for log in logs) / len(logs) if logs else 0,
			"by_model": {}
		}
		
		# Group by model
		for log in logs:
			if log.model not in summary["by_model"]:
				summary["by_model"][log.model] = {
					"requests": 0,
					"cost_units": 0
				}
			summary["by_model"][log.model]["requests"] += 1
			summary["by_model"][log.model]["cost_units"] += log.request_cost_units
		
		return summary

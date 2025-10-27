# Copyright (c) 2025, sammish.thundiyil@gmail.com and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
import requests
import json


class AIModelProfile(Document):
	"""
	AI Model Profile DocType for managing AI model endpoints.
	Handles health checks, capacity tracking, and routing configuration.
	"""
	
	def validate(self):
		"""Validate model profile"""
		self.validate_capacity_score()
		self.validate_cost()
		self.validate_endpoint()
	
	def validate_capacity_score(self):
		"""Ensure capacity score is within bounds"""
		if self.capacity_score < 0 or self.capacity_score > 100:
			frappe.throw("Capacity score must be between 0 and 100")
	
	def validate_cost(self):
		"""Ensure cost is positive"""
		if self.cost_per_unit < 0:
			frappe.throw("Cost per unit cannot be negative")
	
	def validate_endpoint(self):
		"""Validate endpoint URL format"""
		if not self.endpoint_url:
			frappe.throw("Endpoint URL is required")
		
		if not (self.endpoint_url.startswith("http://") or self.endpoint_url.startswith("https://")):
			frappe.throw("Endpoint URL must start with http:// or https://")
	
	def perform_health_check(self):
		"""Perform health check on model endpoint"""
		try:
			import time
			start_time = time.time()
			
			# Simple ping to health endpoint or base endpoint
			health_url = self.endpoint_url.rstrip('/') + '/health'
			
			try:
				response = requests.get(health_url, timeout=5)
				if response.status_code == 200:
					status = "Up"
				elif response.status_code == 503:
					status = "Degraded"
				else:
					status = "Down"
			except:
				# Try base endpoint
				response = requests.get(self.endpoint_url, timeout=5)
				status = "Up" if response.status_code < 500 else "Down"
			
			latency = int((time.time() - start_time) * 1000)
			
			# Update health status
			self.db_set("health_status", status, update_modified=False)
			self.db_set("avg_latency_ms", latency, update_modified=False)
			self.db_set("last_health_check", frappe.utils.now(), update_modified=False)
			frappe.db.commit()
			
			return {
				"status": status,
				"latency_ms": latency,
				"timestamp": frappe.utils.now()
			}
			
		except Exception as e:
			self.db_set("health_status", "Down", update_modified=False)
			self.db_set("last_health_check", frappe.utils.now(), update_modified=False)
			frappe.db.commit()
			
			return {
				"status": "Down",
				"error": str(e),
				"timestamp": frappe.utils.now()
			}
	
	def update_stats(self, success=True, latency_ms=None):
		"""Update model statistics"""
		self.db_set("total_requests", (self.total_requests or 0) + 1, update_modified=False)
		
		if not success:
			self.db_set("failed_requests", (self.failed_requests or 0) + 1, update_modified=False)
		
		# Update success rate
		total = self.total_requests or 1
		failed = self.failed_requests or 0
		success_rate = ((total - failed) / total) * 100
		self.db_set("success_rate", success_rate, update_modified=False)
		
		# Update average latency (rolling average)
		if latency_ms:
			current_avg = self.avg_latency_ms or 0
			new_avg = ((current_avg * (total - 1)) + latency_ms) / total
			self.db_set("avg_latency_ms", int(new_avg), update_modified=False)
		
		frappe.db.commit()
	
	def get_routing_score(self, subscription_priority=0):
		"""
		Calculate routing score based on multiple factors.
		Higher score = better candidate for routing.
		"""
		if not self.is_active or self.health_status == "Down":
			return 0
		
		# Weights for scoring
		WEIGHT_LATENCY = 1.0
		WEIGHT_CAPACITY = 0.5
		WEIGHT_COST = 1.5
		WEIGHT_PRIORITY = 2.0
		WEIGHT_SUCCESS = 0.3
		
		# Latency score (lower is better, inverse it)
		latency_score = WEIGHT_LATENCY * (1.0 / ((self.avg_latency_ms or 100) + 1))
		
		# Capacity score (higher is better)
		capacity_score = WEIGHT_CAPACITY * (self.capacity_score / 100.0)
		
		# Cost score (lower cost is better, inverse it)
		cost_score = -WEIGHT_COST * float(self.cost_per_unit or 0)
		
		# Priority score from subscription
		priority_score = WEIGHT_PRIORITY * subscription_priority
		
		# Success rate score
		success_score = WEIGHT_SUCCESS * ((self.success_rate or 100) / 100.0)
		
		# Degraded penalty
		degraded_penalty = 0
		if self.health_status == "Degraded":
			degraded_penalty = -10
		
		total_score = (latency_score + capacity_score + cost_score + 
		               priority_score + success_score + degraded_penalty)
		
		return total_score
	
	@staticmethod
	def get_best_model(allowed_models, subscription_priority=0):
		"""Get the best model from allowed list based on routing score"""
		models = frappe.get_all(
			"AI Model Profile",
			filters={
				"model_name": ["in", allowed_models],
				"is_active": 1,
				"health_status": ["!=", "Down"]
			},
			fields=["name", "model_name", "endpoint_url", "capacity_score", 
			        "cost_per_unit", "avg_latency_ms", "health_status", "success_rate"]
		)
		
		if not models:
			return None
		
		# Calculate scores for each model
		scored_models = []
		for model in models:
			model_doc = frappe.get_doc("AI Model Profile", model.name)
			score = model_doc.get_routing_score(subscription_priority)
			scored_models.append({
				"model": model_doc,
				"score": score
			})
		
		# Sort by score (highest first)
		scored_models.sort(key=lambda x: x["score"], reverse=True)
		
		return scored_models[0]["model"] if scored_models else None

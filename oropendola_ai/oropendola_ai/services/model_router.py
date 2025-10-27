# Copyright (c) 2025, sammish.thundiyil@gmail.com and contributors
# For license information, please see license.txt

"""
Model Routing Service
Intelligent routing layer that selects the best AI model based on:
- Health status
- Latency
- Cost
- Subscription priority
- Current capacity
"""

import frappe
import os
import time
import requests
import hashlib
from typing import Dict, List, Optional, Tuple


# Redis connection (lazy loaded)
_redis_client = None

def get_redis():
	"""Get Redis connection"""
	global _redis_client
	if _redis_client is None:
		import redis
		redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
		_redis_client = redis.from_url(redis_url, decode_responses=True)
	return _redis_client


class ModelRouter:
	"""
	Intelligent model routing service.
	Handles API key validation, quota checking, model selection, and request routing.
	"""
	
	def __init__(self):
		self.redis = get_redis()
		self.cache_ttl = 60  # Cache TTL in seconds
		
		# Routing weights (configurable via environment variables)
		self.weights = {
			"latency": float(os.getenv("WEIGHT_LATENCY", "1.0")),
			"capacity": float(os.getenv("WEIGHT_CAPACITY", "0.5")),
			"cost": float(os.getenv("WEIGHT_COST", "1.5")),
			"priority": float(os.getenv("WEIGHT_PRIORITY", "2.0"))
		}
	
	def validate_api_key(self, api_key: str) -> Optional[Dict]:
		"""
		Validate API key and return subscription details.
		Uses Redis cache for performance.
		
		Args:
			api_key (str): Raw API key from request
			
		Returns:
			dict: Subscription details or None if invalid
		"""
		# Check cache first
		cache_key = f"api_key:{api_key[:16]}"
		cached_data = self.redis.get(cache_key)
		
		if cached_data:
			import json
			return json.loads(cached_data)
		
		# Validate with Frappe
		key_hash = hashlib.sha256(api_key.encode()).hexdigest()
		
		api_key_docs = frappe.get_all(
			"AI API Key",
			filters={"key_hash": key_hash, "status": "Active"},
			fields=["name", "subscription", "customer"]
		)
		
		if not api_key_docs:
			return None
		
		api_key_doc = api_key_docs[0]
		
		# Get subscription details
		subscription = frappe.get_doc("AI Subscription", api_key_doc.subscription)
		
		if not subscription.is_active():
			return None
		
		# Get plan details
		plan = subscription.get_plan_details()
		
		# Prepare subscription data
		sub_data = {
			"subscription_id": subscription.name,
			"customer": subscription.customer,
			"plan_id": subscription.plan,
			"priority_score": subscription.priority_score,
			"daily_quota_limit": subscription.daily_quota_limit,
			"daily_quota_remaining": subscription.daily_quota_remaining,
			"allowed_models": plan.get_allowed_models(),
			"rate_limit_qps": plan.rate_limit_qps or 0,
			"status": subscription.status
		}
		
		# Cache for performance
		import json
		self.redis.setex(cache_key, self.cache_ttl, json.dumps(sub_data))
		
		return sub_data
	
	def check_quota(self, subscription_id: str, cost_units: float = 1.0) -> Tuple[bool, str]:
		"""
		Check and consume quota.
		Uses Redis for atomic operations.
		
		Args:
			subscription_id (str): Subscription ID
			cost_units (float): Units to consume
			
		Returns:
			tuple: (success: bool, message: str)
		"""
		# Get today's date key
		today = time.strftime("%Y-%m-%d")
		quota_key = f"quota:{subscription_id}:{today}"
		
		# Check if quota key exists
		remaining = self.redis.get(quota_key)
		
		if remaining is None:
			# Initialize from Frappe
			subscription = frappe.get_doc("AI Subscription", subscription_id)
			
			if subscription.daily_quota_limit == -1:
				# Unlimited quota
				self.redis.setex(quota_key, 86400, -1)
				return (True, "Unlimited quota")
			
			# Set quota for today
			self.redis.setex(quota_key, 86400, subscription.daily_quota_limit)
			remaining = subscription.daily_quota_limit
		
		remaining = int(remaining)
		
		# Check unlimited
		if remaining == -1:
			return (True, "Unlimited quota")
		
		# Check if enough quota
		if remaining < cost_units:
			return (False, f"Insufficient quota. Remaining: {remaining}, Required: {cost_units}")
		
		# Consume quota atomically
		new_remaining = self.redis.decr(quota_key, int(cost_units))
		
		return (True, f"Quota consumed. Remaining: {new_remaining}")
	
	def check_rate_limit(self, subscription_id: str, qps_limit: int) -> Tuple[bool, str]:
		"""
		Check rate limit using token bucket algorithm.
		
		Args:
			subscription_id (str): Subscription ID
			qps_limit (int): Queries per second limit
			
		Returns:
			tuple: (allowed: bool, message: str)
		"""
		if qps_limit == 0:
			return (True, "No rate limit")
		
		# Token bucket key
		bucket_key = f"ratelimit:{subscription_id}"
		
		# Lua script for atomic token bucket
		lua_script = """
		local key = KEYS[1]
		local limit = tonumber(ARGV[1])
		local current = tonumber(redis.call('GET', key) or limit)
		
		if current > 0 then
			redis.call('DECR', key)
			redis.call('EXPIRE', key, 1)
			return 1
		else
			return 0
		end
		"""
		
		result = self.redis.eval(lua_script, 1, bucket_key, qps_limit)
		
		if result == 1:
			return (True, "Rate limit passed")
		else:
			return (False, "Rate limit exceeded")
	
	def select_model(self, allowed_models: List[str], priority_score: int) -> Optional[Dict]:
		"""
		Select best model based on routing algorithm.
		
		Args:
			allowed_models (list): List of allowed model names
			priority_score (int): Subscription priority score
			
		Returns:
			dict: Selected model profile or None
		"""
		# Get active models
		models = frappe.get_all(
			"AI Model Profile",
			filters={
				"model_name": ["in", allowed_models],
				"is_active": 1,
				"health_status": ["!=", "Down"]
			},
			fields=["name", "model_name", "endpoint_url", "capacity_score",
			        "cost_per_unit", "avg_latency_ms", "health_status"]
		)
		
		if not models:
			return None
		
		# Score each model
		scored_models = []
		for model in models:
			model_doc = frappe.get_doc("AI Model Profile", model.name)
			score = model_doc.get_routing_score(priority_score)
			
			scored_models.append({
				"model": model_doc,
				"score": score
			})
		
		# Sort by score (highest first)
		scored_models.sort(key=lambda x: x["score"], reverse=True)
		
		return scored_models[0]["model"] if scored_models else None
	
	def route_request(self, api_key: str, payload: dict) -> dict:
		"""
		Main routing function.
		Validates, checks quotas, selects model, and routes request.
		
		Args:
			api_key (str): API key from request
			payload (dict): Request payload
			
		Returns:
			dict: Response with model output or error
		"""
		start_time = time.time()
		
		# Step 1: Validate API key
		subscription = self.validate_api_key(api_key)
		if not subscription:
			return {
				"status": 401,
				"error": "Invalid or expired API key"
			}
		
		# Step 2: Check rate limit
		if subscription["rate_limit_qps"] > 0:
			rate_ok, rate_msg = self.check_rate_limit(
				subscription["subscription_id"],
				subscription["rate_limit_qps"]
			)
			if not rate_ok:
				return {
					"status": 429,
					"error": "Rate limit exceeded",
					"message": rate_msg
				}
		
		# Step 3: Check quota
		cost_units = payload.get("cost_units", 1.0)
		quota_ok, quota_msg = self.check_quota(subscription["subscription_id"], cost_units)
		
		if not quota_ok:
			return {
				"status": 429,
				"error": "Quota exceeded",
				"message": quota_msg
			}
		
		# Step 4: Select model
		selected_model = self.select_model(
			subscription["allowed_models"],
			subscription["priority_score"]
		)
		
		if not selected_model:
			return {
				"status": 503,
				"error": "No available models",
				"message": "All models are down or unavailable"
			}
		
		# Step 5: Make request to model
		try:
			model_start = time.time()
			
			response = requests.post(
				selected_model.endpoint_url,
				json=payload,
				timeout=selected_model.timeout_seconds
			)
			
			model_latency = int((time.time() - model_start) * 1000)
			
			if response.status_code == 200:
				# Success - log usage
				self.log_usage(
					subscription["subscription_id"],
					selected_model.model_name,
					cost_units,
					"Success",
					model_latency,
					tokens_input=payload.get("tokens_input"),
					tokens_output=response.json().get("tokens_output")
				)
				
				# Update model stats
				selected_model.update_stats(success=True, latency_ms=model_latency)
				
				total_time = int((time.time() - start_time) * 1000)
				
				return {
					"status": 200,
					"model": selected_model.model_name,
					"response": response.json(),
					"latency_ms": model_latency,
					"total_time_ms": total_time
				}
			else:
				raise Exception(f"Model returned {response.status_code}")
		
		except Exception as e:
			# Failure - try fallback models
			fallback_result = self.try_fallback_models(
				subscription["allowed_models"],
				subscription["priority_score"],
				selected_model.model_name,
				payload,
				subscription["subscription_id"],
				cost_units
			)
			
			if fallback_result:
				return fallback_result
			
			# All models failed
			self.log_usage(
				subscription["subscription_id"],
				selected_model.model_name,
				cost_units,
				"Failed",
				None,
				error_message=str(e)
			)
			
			selected_model.update_stats(success=False)
			
			return {
				"status": 503,
				"error": "All models failed",
				"message": str(e)
			}
	
	def try_fallback_models(self, allowed_models: List[str], priority_score: int,
	                        failed_model: str, payload: dict, subscription_id: str,
	                        cost_units: float) -> Optional[dict]:
		"""Try fallback models when primary fails"""
		
		# Get other models
		other_models = [m for m in allowed_models if m != failed_model]
		
		for model_name in other_models:
			try:
				model = frappe.get_doc("AI Model Profile", model_name)
				
				if not model.is_active or model.health_status == "Down":
					continue
				
				response = requests.post(
					model.endpoint_url,
					json=payload,
					timeout=model.timeout_seconds
				)
				
				if response.status_code == 200:
					latency = int(response.elapsed.total_seconds() * 1000)
					
					self.log_usage(
						subscription_id,
						model.model_name,
						cost_units,
						"Success",
						latency
					)
					
					model.update_stats(success=True, latency_ms=latency)
					
					return {
						"status": 200,
						"model": model.model_name,
						"response": response.json(),
						"fallback": True
					}
			
			except Exception:
				continue
		
		return None
	
	def log_usage(self, subscription_id: str, model: str, cost_units: float,
	              status: str, latency_ms: Optional[int] = None,
	              error_message: Optional[str] = None,
	              tokens_input: Optional[int] = None,
	              tokens_output: Optional[int] = None):
		"""Log usage asynchronously to Frappe"""
		try:
			# Use Frappe's enqueue to log asynchronously
			frappe.enqueue(
				"oropendola_ai.oropendola_ai.doctype.ai_usage_log.ai_usage_log.AIUsageLog.log_request",
				subscription=subscription_id,
				model=model,
				cost_units=cost_units,
				status=status,
				latency_ms=latency_ms,
				error_message=error_message,
				tokens_input=tokens_input,
				tokens_output=tokens_output,
				queue="short",
				is_async=True
			)
		except Exception as e:
			frappe.log_error(f"Failed to log usage: {str(e)}", "Usage Logging Error")


# Singleton router instance
_router = None

def get_router():
	"""Get singleton ModelRouter instance"""
	global _router
	if _router is None:
		_router = ModelRouter()
	return _router


@frappe.whitelist(allow_guest=True)
def route(api_key: str, payload: dict):
	"""
	Main routing endpoint.
	Called by external services with API key.
	
	Args:
		api_key (str): API key
		payload (dict): Request payload
		
	Returns:
		dict: Response
	"""
	router = get_router()
	return router.route_request(api_key, payload)

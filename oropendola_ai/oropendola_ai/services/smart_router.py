# Copyright (c) 2025, sammish.thundiyil@gmail.com and contributors
# For license information, please see license.txt

"""
Smart Routing Service - Enhanced Model Selection
Adds intelligent routing modes on top of base model router:
- Auto: Dynamic task-based routing
- Performance: Quality-first (Claude/GPT-4 priority)
- Efficient: Cost-first (DeepSeek priority)
- Lite: Free-tier only

Optimized for INR 1,200/month budget (~$14.29 USD)
"""

import frappe
import hashlib
import re
from typing import Dict, List, Optional, Tuple
from oropendola_ai.oropendola_ai.services.model_router import get_router


class SmartRouter:
	"""
	Intelligent routing with task complexity analysis and session continuity.
	Extends base ModelRouter with smart modes.
	"""
	
	def __init__(self):
		self.base_router = get_router()
		self.redis = self.base_router.redis
		
		# Routing mode weights
		self.mode_weights = {
			"auto": self._get_auto_weights,
			"performance": self._get_performance_weights,
			"efficient": self._get_efficient_weights,
			"lite": self._get_lite_weights
		}
		
		# Task complexity patterns
		self.complexity_patterns = {
			"simple": [
				r"what is",
				r"explain briefly",
				r"todo",
				r"list",
				r"simple",
				r"quick",
			],
			"reasoning": [
				r"debug",
				r"test",
				r"unit test",
				r"algorithm",
				r"logic",
				r"calculate",
			],
			"complex": [
				r"review",
				r"architecture",
				r"design pattern",
				r"refactor",
				r"optimize",
				r"comprehensive",
			],
			"multimodal": [
				r"visualize",
				r"diagram",
				r"chart",
				r"image",
				r"screenshot",
			]
		}
	
	def detect_task_complexity(self, prompt: str, context_tokens: int = 0) -> str:
		"""
		Detect task complexity from prompt text.
		
		Args:
			prompt (str): User's prompt
			context_tokens (int): Estimated token count
			
		Returns:
			str: Complexity level (simple, reasoning, complex, multimodal)
		"""
		prompt_lower = prompt.lower()
		
		# Check for multimodal keywords
		for pattern in self.complexity_patterns["multimodal"]:
			if re.search(pattern, prompt_lower):
				return "multimodal"
		
		# Check for complex keywords
		for pattern in self.complexity_patterns["complex"]:
			if re.search(pattern, prompt_lower):
				return "complex"
		
		# Check for reasoning keywords
		for pattern in self.complexity_patterns["reasoning"]:
			if re.search(pattern, prompt_lower):
				return "reasoning"
		
		# Check token count
		if context_tokens > 10000:  # Large context
			return "complex"
		elif context_tokens > 5000:
			return "reasoning"
		
		# Check prompt length
		if len(prompt) < 100:
			return "simple"
		elif len(prompt) < 500:
			return "reasoning"
		else:
			return "complex"
	
	def get_session_model(self, session_id: str) -> Optional[str]:
		"""
		Get cached model for session continuity.
		
		Args:
			session_id (str): Session identifier
			
		Returns:
			str: Model name or None
		"""
		cache_key = f"session:{session_id}:model"
		return self.redis.get(cache_key)
	
	def set_session_model(self, session_id: str, model_name: str, ttl: int = 3600):
		"""
		Cache model for session continuity.
		
		Args:
			session_id (str): Session identifier
			model_name (str): Model to cache
			ttl (int): Time to live in seconds (default: 1 hour)
		"""
		cache_key = f"session:{session_id}:model"
		self.redis.setex(cache_key, ttl, model_name)
	
	def check_context_correlation(self, session_id: str, current_prompt: str) -> float:
		"""
		Check similarity between current and previous prompt.
		Uses simple hash-based similarity for performance.
		
		Args:
			session_id (str): Session identifier
			current_prompt (str): Current user prompt
			
		Returns:
			float: Similarity score (0.0 - 1.0)
		"""
		cache_key = f"session:{session_id}:last_prompt"
		last_prompt = self.redis.get(cache_key)
		
		if not last_prompt:
			# First prompt in session
			self.redis.setex(cache_key, 3600, current_prompt)
			return 0.0
		
		# Simple token-based similarity
		current_tokens = set(current_prompt.lower().split())
		last_tokens = set(last_prompt.lower().split())
		
		if not current_tokens or not last_tokens:
			return 0.0
		
		intersection = current_tokens.intersection(last_tokens)
		union = current_tokens.union(last_tokens)
		
		similarity = len(intersection) / len(union) if union else 0.0
		
		# Update cache
		self.redis.setex(cache_key, 3600, current_prompt)
		
		return similarity
	
	def _get_auto_weights(self, complexity: str) -> Dict[str, float]:
		"""
		Auto mode: Dynamic weights based on task complexity.
		Balances cost (~INR 1,000) and quality.
		"""
		weights = {
			"simple": {
				"DeepSeek": 80,  # 80% routing to cheapest
				"Grok": 10,
				"Gemini": 5,
				"Claude": 3,
				"GPT-4": 2
			},
			"reasoning": {
				"DeepSeek": 40,
				"Grok": 40,      # Grok-fast for reasoning
				"Gemini": 10,
				"Claude": 7,
				"GPT-4": 3
			},
			"complex": {
				"Claude": 50,    # Claude best for reviews
				"GPT-4": 25,
				"Gemini": 15,
				"Grok": 8,
				"DeepSeek": 2
			},
			"multimodal": {
				"Gemini": 70,    # Best for visuals + 1M context
				"Claude": 15,
				"GPT-4": 10,
				"Grok": 3,
				"DeepSeek": 2
			}
		}
		
		return weights.get(complexity, weights["simple"])
	
	def _get_performance_weights(self, complexity: str) -> Dict[str, float]:
		"""
		Performance mode: Quality-first routing.
		Prioritizes Claude/GPT-4 (5-10% of requests).
		"""
		return {
			"Claude": 60,
			"GPT-4": 30,
			"Gemini": 8,
			"Grok": 2,
			"DeepSeek": 0  # Avoid unless necessary
		}
	
	def _get_efficient_weights(self, complexity: str) -> Dict[str, float]:
		"""
		Efficient mode: Cost-first routing.
		80%+ DeepSeek, Grok-fast for reasoning.
		"""
		if complexity == "reasoning":
			return {
				"DeepSeek": 60,
				"Grok": 35,
				"Gemini": 3,
				"Claude": 2,
				"GPT-4": 0
			}
		else:
			return {
				"DeepSeek": 90,
				"Grok": 8,
				"Gemini": 2,
				"Claude": 0,
				"GPT-4": 0
			}
	
	def _get_lite_weights(self, complexity: str) -> Dict[str, float]:
		"""
		Lite mode: Free-tier only.
		Uses Grok free tier or DeepSeek's cheapest.
		"""
		return {
			"Grok": 70,      # Assuming free tier via X
			"DeepSeek": 30,  # Cheapest fallback
			"Gemini": 0,
			"Claude": 0,
			"GPT-4": 0
		}
	
	def apply_mode_weights_to_plan(self, plan_id: str, mode: str, complexity: str):
		"""
		Temporarily override plan's cost weights based on smart routing mode.
		
		Args:
			plan_id (str): AI Plan ID
			mode (str): Routing mode (auto, performance, efficient, lite)
			complexity (str): Task complexity
		"""
		# Get mode-specific weights
		weight_func = self.mode_weights.get(mode, self._get_auto_weights)
		mode_weights = weight_func(complexity)
		
		# Cache the override weights
		cache_key = f"smart_mode:{plan_id}:weights"
		import json
		self.redis.setex(cache_key, 300, json.dumps(mode_weights))  # 5 min cache
		
		return mode_weights
	
	def smart_route(self, api_key: str, payload: dict, mode: str = "auto", 
	                session_id: Optional[str] = None) -> dict:
		"""
		Smart routing with task complexity analysis and session continuity.
		
		Args:
			api_key (str): API key
			payload (dict): Request payload with messages
			mode (str): Routing mode (auto, performance, efficient, lite)
			session_id (str): Optional session ID for continuity
			
		Returns:
			dict: Response with model selection metadata
		"""
		# Extract prompt from payload
		messages = payload.get("messages", [])
		if not messages:
			return {
				"status": 400,
				"error": "No messages provided"
			}
		
		# Get last user message
		user_messages = [m for m in messages if m.get("role") == "user"]
		if not user_messages:
			return {
				"status": 400,
				"error": "No user message found"
			}
		
		current_prompt = user_messages[-1].get("content", "")
		
		# Estimate token count (rough: 1 token ≈ 4 chars)
		context_tokens = sum(len(m.get("content", "")) for m in messages) // 4
		
		# Get subscription to retrieve plan configuration
		subscription = self.base_router.validate_api_key(api_key)
		if not subscription:
			return {
				"status": 401,
				"error": "Invalid API key"
			}
		
		# Get AI Plan configuration
		plan = frappe.get_doc("AI Plan", subscription["plan_id"])
		routing_config = plan.get_smart_routing_config()
		
		# Use mode from parameter or plan default
		effective_mode = mode or routing_config["default_mode"]
		
		# Detect task complexity (if enabled in plan)
		if routing_config["enable_task_complexity_detection"]:
			complexity = self.detect_task_complexity(current_prompt, context_tokens)
		else:
			complexity = "simple"  # Default fallback
		
		# Check session continuity (if enabled in plan)
		use_cached_model = False
		if session_id and routing_config["enable_session_continuity"]:
			correlation = self.check_context_correlation(session_id, current_prompt)
			correlation_threshold = routing_config["correlation_threshold"]
			
			if correlation > correlation_threshold:
				# High correlation - use same model for consistency
				cached_model = self.get_session_model(session_id)
				if cached_model:
					use_cached_model = True
					frappe.log_error(
						f"Session continuity: Using cached model {cached_model} (correlation: {correlation})",
						"Smart Router"
					)
		
		# Get subscription to apply smart weights
		subscription = self.base_router.validate_api_key(api_key)
		if not subscription:
			return {
				"status": 401,
				"error": "Invalid API key"
			}
		
		# Apply smart routing mode weights
		mode_weights = self.apply_mode_weights_to_plan(
			subscription["plan_id"],
			effective_mode,
			complexity
		)
		
		# Update cost weights in-memory (temporary)
		for model_access in plan.model_access:
			if model_access.model_name in mode_weights:
				model_access.cost_weight = mode_weights[model_access.model_name]
		
		# Route through base router (which will use overridden weights)
		result = self.base_router.route_request(api_key, payload)
		
		# Add smart routing metadata
		if result.get("status") == 200:
			result["smart_mode"] = effective_mode
			result["task_complexity"] = complexity
			result["mode_weights_applied"] = mode_weights
			result["plan_config_used"] = {
				"default_mode": routing_config["default_mode"],
				"session_continuity_enabled": routing_config["enable_session_continuity"],
				"complexity_detection_enabled": routing_config["enable_task_complexity_detection"]
			}
			
			# Cache model for session continuity (if enabled)
			if session_id and routing_config["enable_session_continuity"] and not use_cached_model:
				ttl = routing_config["session_ttl"]
				self.set_session_model(session_id, result["model"], ttl)
		
		return result


# Singleton instance
_smart_router = None

def get_smart_router():
	"""Get singleton SmartRouter instance"""
	global _smart_router
	if _smart_router is None:
		_smart_router = SmartRouter()
	return _smart_router


@frappe.whitelist(allow_guest=True)
def smart_route(api_key: str, payload: dict, mode: str = "auto", session_id: str = None):
	"""
	Smart routing endpoint with mode selection.
	
	Args:
		api_key (str): API key
		payload (dict): Request payload
		mode (str): Routing mode (auto, performance, efficient, lite)
		session_id (str): Optional session ID
		
	Returns:
		dict: Response
	"""
	router = get_smart_router()
	return router.smart_route(api_key, payload, mode, session_id)

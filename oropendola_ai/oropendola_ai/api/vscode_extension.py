# Copyright (c) 2025, sammish.thundiyil@gmail.com and contributors
# For license information, please see license.txt

"""
VS Code Extension API Endpoints
Provides RESTful API for Oropendola AI VS Code Extension
"""

import frappe
from frappe import _
import json


# ========================================
# Authentication & API Key Management
# ========================================

@frappe.whitelist(allow_guest=True)
def validate_api_key(api_key: str):
	"""
	Validate API key for VS Code extension
	
	Args:
		api_key (str): API key from VS Code extension
		
	Returns:
		dict: Validation result with subscription details
	"""
	try:
		from oropendola_ai.oropendola_ai.services.model_router import get_router
		
		router = get_router()
		subscription = router.validate_api_key(api_key)
		
		if subscription:
			return {
				"valid": True,
				"subscription_id": subscription["subscription_id"],
				"customer": subscription["customer"],
				"plan_id": subscription["plan_id"],
				"daily_quota_remaining": subscription["daily_quota_remaining"],
				"allowed_models": subscription["allowed_models"],
				"status": subscription["status"]
			}
		else:
			return {
				"valid": False,
				"error": "Invalid or expired API key"
			}
	
	except Exception as e:
		frappe.log_error(message=str(e), title="VS Code API Key Validation Error")
		return {
			"valid": False,
			"error": str(e)
		}


@frappe.whitelist()
def get_api_keys():
	"""
	Get all API keys for current user
	
	Returns:
		list: List of API keys with details
	"""
	user = frappe.session.user
	
	# Get customer for current user
	customer = frappe.db.get_value("AI Customer", {"email": user})
	
	if not customer:
		frappe.throw(_("No customer account found for this user"))
	
	# Get all API keys
	api_keys = frappe.get_all(
		"AI API Key",
		filters={"customer": customer},
		fields=["name", "key_name", "status", "created_at", "last_used", "subscription"]
	)
	
	return api_keys


@frappe.whitelist()
def create_api_key(key_name: str, subscription: str):
	"""
	Create new API key for VS Code extension
	
	Args:
		key_name (str): Name for the API key
		subscription (str): Subscription ID
		
	Returns:
		dict: New API key details
	"""
	user = frappe.session.user
	
	# Get customer for current user
	customer = frappe.db.get_value("AI Customer", {"email": user})
	
	if not customer:
		frappe.throw(_("No customer account found for this user"))
	
	# Verify subscription belongs to customer
	sub_customer = frappe.db.get_value("AI Subscription", subscription, "customer")
	if sub_customer != customer:
		frappe.throw(_("Invalid subscription"))
	
	# Create API key
	from oropendola_ai.oropendola_ai.doctype.ai_api_key.ai_api_key import AIAPIKey
	
	api_key = AIAPIKey.generate_key(
		customer=customer,
		subscription=subscription,
		key_name=key_name
	)
	
	return {
		"key_name": key_name,
		"api_key": api_key,
		"subscription": subscription,
		"message": "API key created successfully. Please save this key securely - it won't be shown again."
	}


# ========================================
# AI Agent Mode - Intelligent Routing
# ========================================

@frappe.whitelist(allow_guest=True)
def agent(api_key: str, prompt: str, context: str = None, mode: str = "auto", 
          session_id: str = None, **kwargs):
	"""
	Agent Mode - Intelligent AI routing with Smart Routing Modes
	Users don't need to select models - Oropendola handles routing automatically
	
	Args:
		api_key (str): API key
		prompt (str): User's request/prompt
		context (str): Additional context (optional)
		mode (str): Routing mode - auto, performance, efficient, lite (default: auto)
		session_id (str): Session ID for continuity (optional)
		**kwargs: Additional parameters (temperature, max_tokens, etc.)
		
	Returns:
		dict: AI response with model selection metadata
	"""
	try:
		# Build messages for AI
		messages = []
		
		if context:
			messages.append({
				"role": "system",
				"content": context
			})
		
		messages.append({
			"role": "user",
			"content": prompt
		})
		
		# Prepare payload
		payload = {
			"messages": messages,
			**kwargs
		}
		
		# Route through smart router
		from oropendola_ai.oropendola_ai.services.smart_router import get_smart_router
		
		router = get_smart_router()
		result = router.smart_route(api_key, payload, mode, session_id)
		
		# Add metadata about agent mode
		if result.get("status") == 200:
			result["agent_mode"] = True
			result["auto_selected"] = True
			result["selection_reason"] = f"Optimized for {result.get('task_complexity', 'general')} tasks in {mode} mode"
		
		return result
	
	except Exception as e:
		frappe.log_error(message=str(e), title="VS Code Agent Mode Error")
		return {
			"status": 500,
			"error": "Agent mode error",
			"message": str(e)
		}

@frappe.whitelist(allow_guest=True)
def chat_completion(api_key: str, model: str = None, messages: str = None, **kwargs):
	"""
	Chat completion endpoint for VS Code extension
	
	Args:
		api_key (str): API key
		model (str): Preferred model name (optional, will auto-select if not provided)
		messages (str): JSON string of messages array
		**kwargs: Additional parameters (temperature, max_tokens, etc.)
		
	Returns:
		dict: AI response
	"""
	try:
		# Parse messages
		if isinstance(messages, str):
			messages = json.loads(messages)
		
		# Prepare payload
		payload = {
			"messages": messages,
			"model": model,
			**kwargs
		}
		
		# Route request through model router
		from oropendola_ai.oropendola_ai.services.model_router import get_router
		
		router = get_router()
		result = router.route_request(api_key, payload)
		
		return result
	
	except Exception as e:
		frappe.log_error(message=str(e), title="VS Code Chat Completion Error")
		return {
			"status": 500,
			"error": "Internal error",
			"message": str(e)
		}


@frappe.whitelist(allow_guest=True)
def code_completion(api_key: str, code: str, language: str, context: str = None):
	"""
	Agent Mode: Code completion
	Automatically routes to best model for code completion tasks
	
	Args:
		api_key (str): API key
		code (str): Code to complete
		language (str): Programming language
		context (str): Additional context (optional)
		
	Returns:
		dict: Code completion response
	"""
	try:
		# Build specialized prompt for code completion
		system_context = f"You are an expert {language} programmer. Complete the following code precisely and efficiently."
		
		if context:
			system_context += f"\n\nAdditional context: {context}"
		
		prompt = f"Complete this {language} code:\n\n{code}"
		
		# Use agent mode - let Oropendola select the best model
		return agent(
			api_key=api_key,
			prompt=prompt,
			context=system_context,
			temperature=0.3  # Lower temperature for code completion
		)
	
	except Exception as e:
		frappe.log_error(message=str(e), title="VS Code Code Completion Error")
		return {
			"status": 500,
			"error": str(e)
		}


@frappe.whitelist(allow_guest=True)
def code_explanation(api_key: str, code: str, language: str):
	"""
	Agent Mode: Code explanation
	Automatically routes to best model for code explanation tasks
	
	Args:
		api_key (str): API key
		code (str): Code to explain
		language (str): Programming language
		
	Returns:
		dict: Code explanation
	"""
	try:
		system_context = f"You are an expert {language} programmer. Explain the following code clearly and concisely."
		prompt = f"Explain this {language} code:\n\n```{language}\n{code}\n```"
		
		# Use agent mode
		return agent(
			api_key=api_key,
			prompt=prompt,
			context=system_context,
			temperature=0.5
		)
	
	except Exception as e:
		frappe.log_error(message=str(e), title="VS Code Code Explanation Error")
		return {
			"status": 500,
			"error": str(e)
		}


@frappe.whitelist(allow_guest=True)
def code_refactor(api_key: str, code: str, language: str, instructions: str):
	"""
	Agent Mode: Code refactoring  
	Automatically routes to best model for code refactoring tasks
	
	Args:
		api_key (str): API key
		code (str): Code to refactor
		language (str): Programming language
		instructions (str): Refactoring instructions
		
	Returns:
		dict: Refactored code
	"""
	try:
		system_context = f"You are an expert {language} programmer. Refactor the following code according to the instructions. Provide only the refactored code."
		prompt = f"Refactoring instructions: {instructions}\n\n```{language}\n{code}\n```"
		
		# Use agent mode
		return agent(
			api_key=api_key,
			prompt=prompt,
			context=system_context,
			temperature=0.4
		)
	
	except Exception as e:
		frappe.log_error(message=str(e), title="VS Code Code Refactor Error")
		return {
			"status": 500,
			"error": str(e)
		}


# ========================================
# Available Models & Configuration
# ========================================

@frappe.whitelist(allow_guest=True)
def get_available_models(api_key: str):
	"""
	Get available AI models for the API key's subscription
	
	Args:
		api_key (str): API key
		
	Returns:
		list: Available models
	"""
	try:
		from oropendola_ai.oropendola_ai.services.model_router import get_router
		
		router = get_router()
		subscription = router.validate_api_key(api_key)
		
		if not subscription:
			return {
				"error": "Invalid API key"
			}
		
		# Get model details
		models = frappe.get_all(
			"AI Model Profile",
			filters={
				"model_name": ["in", subscription["allowed_models"]],
				"is_active": 1
			},
			fields=["model_name", "provider", "capacity_score", "max_context_window", "supports_streaming"]
		)
		
		return {
			"models": models,
			"default_model": models[0]["model_name"] if models else None
		}
	
	except Exception as e:
		frappe.log_error(message=str(e), title="VS Code Get Models Error")
		return {
			"error": str(e)
		}


# ========================================
# Usage & Quota Information
# ========================================

@frappe.whitelist(allow_guest=True)
def get_usage_stats(api_key: str):
	"""
	Get usage statistics for API key
	
	Args:
		api_key (str): API key
		
	Returns:
		dict: Usage statistics
	"""
	try:
		from oropendola_ai.oropendola_ai.services.model_router import get_router
		
		router = get_router()
		subscription = router.validate_api_key(api_key)
		
		if not subscription:
			return {
				"error": "Invalid API key"
			}
		
		# Get subscription details
		sub = frappe.get_doc("AI Subscription", subscription["subscription_id"])
		
		return {
			"daily_quota_limit": subscription["daily_quota_limit"],
			"daily_quota_remaining": subscription["daily_quota_remaining"],
			"daily_quota_used": subscription["daily_quota_limit"] - subscription["daily_quota_remaining"] if subscription["daily_quota_limit"] != -1 else 0,
			"status": subscription["status"],
			"plan": subscription["plan_id"]
		}
	
	except Exception as e:
		frappe.log_error(message=str(e), title="VS Code Usage Stats Error")
		return {
			"error": str(e)
		}


# ========================================
# Health Check
# ========================================

@frappe.whitelist(allow_guest=True)
def health_check():
	"""
	Health check endpoint for VS Code extension
	
	Returns:
		dict: Service health status
	"""
	return {
		"status": "healthy",
		"service": "Oropendola AI",
		"version": "1.0.0",
		"timestamp": frappe.utils.now()
	}

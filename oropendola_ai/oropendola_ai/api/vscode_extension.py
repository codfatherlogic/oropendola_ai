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
def initiate_vscode_auth():
	"""
	Initiate authentication flow for VS Code extension
	Generates a session token and returns the authentication URL
	
	Returns:
		dict: Session token and auth URL
	"""
	try:
		import secrets
		
		# Generate secure session token
		session_token = secrets.token_urlsafe(32)
		
		# Store session in cache (expires in 10 minutes)
		cache_key = f"vscode_auth:{session_token}"
		frappe.cache().set_value(cache_key, {
			"status": "pending",
			"created_at": frappe.utils.now(),
			"user": None,
			"api_key": None,
			"subscription": None
		}, expires_in_sec=600)
		
		# Build authentication URL
		auth_url = f"{frappe.utils.get_url()}/vscode-auth?token={session_token}"
		
		return {
			"success": True,
			"auth_url": auth_url,
			"session_token": session_token,
			"expires_in": 600
		}
		
	except Exception as e:
		frappe.log_error(message=str(e), title="VS Code Auth Initiation Error")
		return {
			"success": False,
			"error": str(e)
		}


@frappe.whitelist(allow_guest=True)
def check_vscode_auth_status(session_token):
	"""
	Check if VS Code authentication is complete
	Polled by VS Code extension every 5 seconds
	
	Args:
		session_token (str): Session token from initiate_vscode_auth
		
	Returns:
		dict: Authentication status and data
	"""
	try:
		cache_key = f"vscode_auth:{session_token}"
		session_data = frappe.cache().get_value(cache_key)
		
		if not session_data:
			return {
				"success": False,
				"status": "expired",
				"message": "Session expired or invalid"
			}
		
		# If authentication is complete, return data and clear cache
		if session_data.get("status") == "complete":
			# Clear the cache after successful retrieval
			frappe.cache().delete_value(cache_key)
			
			return {
				"success": True,
				"status": "complete",
				"api_key": session_data.get("api_key"),
				"user_email": session_data.get("user"),
				"subscription": session_data.get("subscription")
			}
		
		# Still pending
		return {
			"success": True,
			"status": session_data.get("status"),
			"message": "Authentication pending"
		}
		
	except Exception as e:
		frappe.log_error(message=str(e), title="VS Code Auth Status Check Error")
		return {
			"success": False,
			"error": str(e)
		}


@frappe.whitelist()
def complete_vscode_auth(session_token, user_email, api_key, subscription):
	"""
	Mark VS Code authentication as complete
	Called by the frontend auth page after successful login
	
	Args:
		session_token (str): Session token
		user_email (str): Logged-in user's email
		api_key (str): User's API key
		subscription (dict): Subscription details
		
	Returns:
		dict: Success status
	"""
	try:
		cache_key = f"vscode_auth:{session_token}"
		session_data = frappe.cache().get_value(cache_key)
		
		if not session_data:
			return {
				"success": False,
				"error": "Invalid or expired session"
			}
		
		# Update session with authentication data
		frappe.cache().set_value(cache_key, {
			"status": "complete",
			"user": user_email,
			"api_key": api_key,
			"subscription": subscription,
			"completed_at": frappe.utils.now()
		}, expires_in_sec=300)  # 5 minutes for VS Code to retrieve
		
		return {
			"success": True,
			"message": "Authentication complete"
		}
		
	except Exception as e:
		frappe.log_error(message=str(e), title="VS Code Auth Completion Error")
		return {
			"success": False,
			"error": str(e)
		}

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
def agent(api_key=None, prompt=None, context=None, mode="auto", session_id=None, **kwargs):
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
		# Handle JSON body data if sent via POST
		import json
		if frappe.request and frappe.request.data:
			try:
				json_data = json.loads(frappe.request.data)
				# Merge JSON data with function args, prioritizing explicit args
				api_key = api_key or json_data.get('api_key')
				prompt = prompt or json_data.get('prompt')
				context = context or json_data.get('context')
				mode = json_data.get('mode', mode)
				session_id = session_id or json_data.get('session_id')
				# Merge any additional kwargs
				kwargs.update({k: v for k, v in json_data.items() if k not in ['api_key', 'prompt', 'context', 'mode', 'session_id', 'cmd']})
			except:
				pass  # Fall back to form_dict params

		# Type conversion and validation
		api_key = str(api_key) if api_key else None
		if not api_key:
			return {
				"status": 400,
				"error": "API key is required"
			}

		# Check if api_key is actually a VS Code access token
		# VS Code extension passes the access token as api_key
		# We need to convert it to the user's actual API key
		try:
			access_token_check = frappe.db.sql("""
				SELECT user
				FROM `tabVS Code Auth Request`
				WHERE access_token = %s AND status = 'Completed'
				LIMIT 1
			""", (api_key,), as_dict=True)

			if access_token_check:
				# This is an access token, not an API key
				# Look up the user's actual API key
				user_email = access_token_check[0].user
				user_api_key = frappe.db.get_value("User", user_email, "api_key")

				if not user_api_key:
					# Generate API key for the user if they don't have one
					user_doc = frappe.get_doc("User", user_email)
					user_api_key = frappe.generate_hash(length=32)
					user_doc.api_key = user_api_key
					user_doc.save(ignore_permissions=True)
					frappe.db.commit()

				# Replace access token with actual API key
				api_key = user_api_key
		except Exception as e:
			frappe.log_error(f"Error converting access token to API key: {str(e)}", "VS Code Agent API")

		# Convert prompt to string if needed
		if prompt is None or prompt == "":
			return {
				"status": 400,
				"error": "Prompt is required"
			}
		prompt = str(prompt)

		# Convert optional parameters
		context = str(context) if context else None
		mode = str(mode) if mode else "auto"
		session_id = str(session_id) if session_id else None

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

		# Handle errors
		if result.get("status") != 200:
			return result

		# Extract AI response from nested structure
		# The router returns: {"status": 200, "response": {...}, "model": "..."}
		# We need to return the actual AI content in a format the VS Code extension understands
		ai_response = result.get("response", {})

		# Check if response has choices (OpenAI format)
		if "choices" in ai_response:
			content = ai_response["choices"][0].get("message", {}).get("content", "")
		# Check if response has content directly
		elif "content" in ai_response:
			content = ai_response["content"]
		# Fallback: return entire response
		else:
			content = str(ai_response)

		# Return in VS Code extension compatible format
		return {
			"status": 200,
			"content": content,
			"model": result.get("model", "auto-selected"),
			"agent_mode": True,
			"auto_selected": True,
			"selection_reason": f"Optimized for {result.get('task_complexity', 'general')} tasks in {mode} mode",
			"task_complexity": result.get("task_complexity"),
			"latency_ms": result.get("latency_ms"),
			"cost": result.get("cost"),
			"budget_remaining": result.get("budget_remaining"),
			"full_response": ai_response  # Include full response for debugging
		}

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
def code_completion(api_key=None, code=None, language=None, context=None):
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
		# Handle JSON body data if sent via POST
		import json
		if frappe.request and frappe.request.data:
			try:
				json_data = json.loads(frappe.request.data)
				api_key = api_key or json_data.get('api_key')
				code = code or json_data.get('code')
				language = language or json_data.get('language')
				context = context or json_data.get('context')
			except:
				pass

		# Type conversion and validation
		api_key = str(api_key) if api_key else None
		if not api_key:
			return {
				"status": 400,
				"error": "API key is required"
			}

		code = str(code) if code else None
		if not code:
			return {
				"status": 400,
				"error": "Code is required"
			}

		language = str(language) if language else "code"
		context = str(context) if context else None

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
def code_explanation(api_key=None, code=None, language=None):
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
		# Handle JSON body data if sent via POST
		import json
		if frappe.request and frappe.request.data:
			try:
				json_data = json.loads(frappe.request.data)
				api_key = api_key or json_data.get('api_key')
				code = code or json_data.get('code')
				language = language or json_data.get('language')
			except:
				pass

		# Type conversion and validation
		api_key = str(api_key) if api_key else None
		if not api_key:
			return {
				"status": 400,
				"error": "API key is required"
			}

		code = str(code) if code else None
		if not code:
			return {
				"status": 400,
				"error": "Code is required"
			}

		language = str(language) if language else "code"

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
def code_refactor(api_key=None, code=None, language=None, instructions=None):
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
		# Handle JSON body data if sent via POST
		import json
		if frappe.request and frappe.request.data:
			try:
				json_data = json.loads(frappe.request.data)
				api_key = api_key or json_data.get('api_key')
				code = code or json_data.get('code')
				language = language or json_data.get('language')
				instructions = instructions or json_data.get('instructions')
			except:
				pass

		# Type conversion and validation
		api_key = str(api_key) if api_key else None
		if not api_key:
			return {
				"status": 400,
				"error": "API key is required"
			}

		code = str(code) if code else None
		if not code:
			return {
				"status": 400,
				"error": "Code is required"
			}

		language = str(language) if language else "code"

		instructions = str(instructions) if instructions else None
		if not instructions:
			return {
				"status": 400,
				"error": "Refactoring instructions are required"
			}

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

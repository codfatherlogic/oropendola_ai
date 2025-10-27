# Copyright (c) 2025, sammish.thundiyil@gmail.com and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def after_install():
	"""Called after app installation"""
	create_default_model_profiles()


@frappe.whitelist()
def setup_default_profiles():
	"""Manual trigger to create default AI Model Profiles (can be called from console or API)"""
	if not frappe.has_permission("AI Model Profile", "create"):
		frappe.throw(_("Insufficient permissions to create AI Model Profiles"))
	
	create_default_model_profiles()
	frappe.msgprint(_("Default AI Model Profiles have been created/verified."))


def create_default_model_profiles():
	"""Create default AI Model Profiles"""
	
	default_models = [
		{
			"model_name": "DeepSeek",
			"provider": "DeepSeek",
			"endpoint_url": "https://api.deepseek.com/v1/chat/completions",
			"api_key_env_var": "DEEPSEEK_API_KEY",
			"capacity_score": 85,
			"cost_per_unit": 0.0014,
			"max_context_window": 128000,
			"supports_streaming": 1,
			"timeout_seconds": 30,
			"max_concurrent_requests": 20,
			"retry_attempts": 3,
			"tags": '["chat", "completion", "reasoning"]',
			"is_active": 1
		},
		{
			"model_name": "Grok",
			"provider": "xAI",
			"endpoint_url": "https://api.x.ai/v1/chat/completions",
			"api_key_env_var": "GROK_API_KEY",
			"capacity_score": 80,
			"cost_per_unit": 0.002,
			"max_context_window": 131072,
			"supports_streaming": 1,
			"timeout_seconds": 30,
			"max_concurrent_requests": 15,
			"retry_attempts": 3,
			"tags": '["chat", "completion", "realtime"]',
			"is_active": 1
		},
		{
			"model_name": "Claude",
			"provider": "Anthropic",
			"endpoint_url": "https://api.anthropic.com/v1/messages",
			"api_key_env_var": "ANTHROPIC_API_KEY",
			"capacity_score": 95,
			"cost_per_unit": 0.003,
			"max_context_window": 200000,
			"supports_streaming": 1,
			"timeout_seconds": 45,
			"max_concurrent_requests": 25,
			"retry_attempts": 3,
			"tags": '["chat", "completion", "analysis", "coding"]',
			"is_active": 1
		},
		{
			"model_name": "GPT-4",
			"provider": "OpenAI",
			"endpoint_url": "https://api.openai.com/v1/chat/completions",
			"api_key_env_var": "OPENAI_API_KEY",
			"capacity_score": 90,
			"cost_per_unit": 0.03,
			"max_context_window": 128000,
			"supports_streaming": 1,
			"timeout_seconds": 40,
			"max_concurrent_requests": 30,
			"retry_attempts": 3,
			"tags": '["chat", "completion", "multimodal"]',
			"is_active": 1
		},
		{
			"model_name": "Gemini",
			"provider": "Google",
			"endpoint_url": "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent",
			"api_key_env_var": "GOOGLE_API_KEY",
			"capacity_score": 88,
			"cost_per_unit": 0.00125,
			"max_context_window": 1000000,
			"supports_streaming": 1,
			"timeout_seconds": 35,
			"max_concurrent_requests": 20,
			"retry_attempts": 3,
			"tags": '["chat", "completion", "multimodal", "long-context"]',
			"is_active": 1
		}
	]
	
	created_count = 0
	existing_count = 0
	failed_count = 0
	
	for model_data in default_models:
		# Check if model already exists
		if not frappe.db.exists("AI Model Profile", model_data["model_name"]):
			try:
				doc = frappe.get_doc({
					"doctype": "AI Model Profile",
					**model_data
				})
				doc.insert(ignore_permissions=True)
				frappe.db.commit()
				created_count += 1
				print(f"✓ Created default AI Model Profile: {model_data['model_name']}")
			except Exception as e:
				failed_count += 1
				frappe.log_error(
					message=f"Failed to create default model profile {model_data['model_name']}: {str(e)}",
					title="Default Model Profile Creation Failed"
				)
				print(f"✗ Failed to create {model_data['model_name']}: {str(e)}")
		else:
			existing_count += 1
			print(f"⊙ AI Model Profile already exists: {model_data['model_name']}")
	
	print(f"\n=== Summary ===")
	print(f"Created: {created_count}")
	print(f"Already exists: {existing_count}")
	print(f"Failed: {failed_count}")

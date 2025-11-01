# Copyright (c) 2025, sammish.thundiyil@gmail.com and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def after_install():
	"""Called after app installation"""
	create_website_user_role()
	create_default_model_profiles()
	create_default_plans()


def create_website_user_role():
	"""Create Website User role if it doesn't exist - required for website users to log in"""
	if frappe.db.exists("Role", "Website User"):
		print("⊙ Website User role already exists")
		return
	
	try:
		# Create the Website User role with desk_access = 0
		role = frappe.get_doc({
			"doctype": "Role",
			"name": "Website User",
			"desk_access": 0
		})
		role.insert(ignore_permissions=True)
		frappe.db.commit()
		print("✓ Created Website User role")
		return True
	except Exception as e:
		frappe.log_error(
			message=f"Failed to create Website User role: {str(e)}",
			title="Website User Role Creation Failed"
		)
		print(f"✗ Failed to create Website User role: {str(e)}")
		return False


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


@frappe.whitelist()
def delete_all_subscriptions_and_keys():
	"""Delete all AI API Keys and AI Subscriptions - USE WITH CAUTION!"""
	try:
		# Delete all AI API Keys
		api_keys = frappe.get_all("AI API Key")
		for key in api_keys:
			frappe.delete_doc("AI API Key", key.name, force=1, ignore_permissions=True)
		
		# Delete all AI Subscriptions
		subscriptions = frappe.get_all("AI Subscription")
		for sub in subscriptions:
			frappe.delete_doc("AI Subscription", sub.name, force=1, ignore_permissions=True)
		
		# Delete all AI Invoices
		invoices = frappe.get_all("AI Invoice")
		for inv in invoices:
			frappe.delete_doc("AI Invoice", inv.name, force=1, ignore_permissions=True)
		
		# Delete all AI Customers
		customers = frappe.get_all("AI Customer")
		for cust in customers:
			frappe.delete_doc("AI Customer", cust.name, force=1, ignore_permissions=True)
		
		frappe.db.commit()
		
		print(f"✓ Deleted {len(api_keys)} API Keys")
		print(f"✓ Deleted {len(subscriptions)} Subscriptions")
		print(f"✓ Deleted {len(invoices)} Invoices")
		print(f"✓ Deleted {len(customers)} Customers")
		
		return {
			"success": True,
			"deleted_keys": len(api_keys),
			"deleted_subscriptions": len(subscriptions),
			"deleted_invoices": len(invoices),
			"deleted_customers": len(customers)
		}
	except Exception as e:
		frappe.db.rollback()
		print(f"✗ Error: {str(e)}")
		return {"success": False, "error": str(e)}


@frappe.whitelist()
def create_default_plans():
	"""Create default AI subscription plans"""
	
	plans_data = [
		{
			"plan_id": "1-day-trial",
			"title": "1 Day Trial",
			"description": "Try Oropendola AI for one day",
			"price": 199,
			"currency": "INR",
			"duration_days": 1,
			"requests_limit_per_day": 200,
			"monthly_budget_limit": 0,
			"support_level": "Standard",
			"default_routing_mode": "efficient",
			"priority_score": 1,
			"is_active": 1,
			"features": [
				"Premium Fast Requests",
				"Smart To-Do List",
				"1M Context Window"
			],
			"models": [
				{"name": "DeepSeek", "cost_weight": 60},
				{"name": "Grok", "cost_weight": 10},
				{"name": "Claude", "cost_weight": 10},
				{"name": "GPT-4", "cost_weight": 10},
				{"name": "Gemini", "cost_weight": 10}
			]
		},
		{
			"plan_id": "7-days",
			"title": "7 Days",
			"description": "Perfect for short projects",
			"price": 849,
			"currency": "INR",
			"duration_days": 7,
			"requests_limit_per_day": 300,
			"monthly_budget_limit": 1000,
			"support_level": "Priority",
			"default_routing_mode": "auto",
			"priority_score": 5,
			"is_active": 1,
			"features": [
				"Premium Fast Requests",
				"Smart To-Do List",
				"1M Context Window"
			],
			"models": [
				{"name": "DeepSeek", "cost_weight": 60},
				{"name": "Grok", "cost_weight": 10},
				{"name": "Claude", "cost_weight": 10},
				{"name": "GPT-4", "cost_weight": 10},
				{"name": "Gemini", "cost_weight": 10}
			]
		},
		{
			"plan_id": "1-month-unlimited",
			"title": "1 Month - Unlimited",
			"description": "Unlimited requests for one month",
			"price": 2999,
			"currency": "INR",
			"duration_days": 30,
			"requests_limit_per_day": -1,
			"monthly_budget_limit": 5000,
			"support_level": "Enterprise",
			"default_routing_mode": "performance",
			"priority_score": 10,
			"is_active": 1,
			"features": [
				"Premium Fast Requests",
				"High-Priority Support",
				"Smart To-Do List",
				"1M Context Window"
			],
			"models": [
				{"name": "DeepSeek", "cost_weight": 60},
				{"name": "Grok", "cost_weight": 10},
				{"name": "Claude", "cost_weight": 10},
				{"name": "GPT-4", "cost_weight": 10},
				{"name": "Gemini", "cost_weight": 10}
			]
		}
	]
	
	created_count = 0
	existing_count = 0
	
	for plan_data in plans_data:
		# Check if plan already exists
		if frappe.db.exists("AI Plan", plan_data["plan_id"]):
			existing_count += 1
			print(f"⊙ AI Plan already exists: {plan_data['title']}")
			continue
		
		# Extract features and models
		features = plan_data.pop("features", [])
		models = plan_data.pop("models", [])
		
		# Create plan
		plan = frappe.get_doc({
			"doctype": "AI Plan",
			"name": plan_data["plan_id"],
			**plan_data
		})
		
		# Add features
		for idx, feature_name in enumerate(features, 1):
			plan.append("features", {
				"feature_name": feature_name,
				"enabled": 1,
				"idx": idx
			})
		
		# Add models with cost weights
		for idx, model_data in enumerate(models, 1):
			if isinstance(model_data, dict):
				# New format with cost weight
				plan.append("model_access", {
					"model_name": model_data["name"],
					"cost_weight": model_data.get("cost_weight", 1),
					"idx": idx
				})
			else:
				# Old format (just model name)
				plan.append("model_access", {
					"model_name": model_data,
					"cost_weight": 1,
					"idx": idx
				})
		
		plan.insert(ignore_permissions=True)
		created_count += 1
		print(f"✓ Created plan: {plan_data['title']}")
	
	frappe.db.commit()
	print(f"\n=== AI Plans Summary ===")
	print(f"Created: {created_count}")
	print(f"Already exists: {existing_count}")
	
	return {
		"success": True,
		"created": created_count,
		"existing": existing_count
	}

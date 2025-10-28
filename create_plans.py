#!/usr/bin/env python3
"""
Create default AI Plans for Oropendola AI
Run this script to populate the database with pricing plans
"""

import frappe

def create_default_plans():
    """Create default AI subscription plans"""
    
    frappe.init(site='oropendola.ai')
    frappe.connect()
    frappe.set_user('Administrator')
    
    plans_data = [
        {
            "plan_id": "free-tier",
            "title": "Free Tier",
            "description": "Perfect for trying out Oropendola AI",
            "price": 0,
            "currency": "INR",
            "duration_days": 30,
            "requests_limit_per_day": 200,
            "monthly_budget_limit": 0,
            "support_level": "Community",
            "default_routing_mode": "cost_optimized",
            "is_active": 1,
            "features": [
                "200 requests/day",
                "5 AI models",
                "Standard support",
                "Auto routing mode"
            ],
            "models": ["gpt-3.5-turbo", "claude-3-haiku", "gemini-pro"]
        },
        {
            "plan_id": "pro-monthly",
            "title": "Pro Plan",
            "description": "For professional developers",
            "price": 1999,
            "currency": "INR",
            "duration_days": 30,
            "requests_limit_per_day": 5000,
            "monthly_budget_limit": 2000,
            "support_level": "Priority",
            "default_routing_mode": "balanced",
            "is_active": 1,
            "features": [
                "5000 requests/day",
                "All AI models",
                "Priority support",
                "Balanced routing",
                "₹2000 monthly budget",
                "Premium Fast Requests"
            ],
            "models": ["gpt-4", "gpt-3.5-turbo", "claude-3-sonnet", "claude-3-haiku", "gemini-pro"]
        },
        {
            "plan_id": "team-monthly",
            "title": "Team Plan",
            "description": "For development teams",
            "price": 9999,
            "currency": "INR",
            "duration_days": 30,
            "requests_limit_per_day": 25000,
            "monthly_budget_limit": 10000,
            "support_level": "Premium",
            "default_routing_mode": "performance",
            "is_active": 1,
            "features": [
                "25000 requests/day",
                "All AI models",
                "Premium support",
                "Performance routing",
                "₹10000 monthly budget",
                "Team collaboration",
                "Advanced analytics"
            ],
            "models": ["gpt-4", "gpt-3.5-turbo", "claude-3-opus", "claude-3-sonnet", "gemini-pro"]
        },
        {
            "plan_id": "corporate",
            "title": "Corporate",
            "description": "Custom enterprise solution",
            "price": 0,  # Custom pricing
            "currency": "INR",
            "duration_days": 365,
            "requests_limit_per_day": -1,  # Unlimited
            "monthly_budget_limit": 0,  # Custom
            "support_level": "Dedicated",
            "default_routing_mode": "performance",
            "is_active": 1,
            "features": [
                "Unlimited requests",
                "All AI models",
                "Dedicated support",
                "Custom routing",
                "Unlimited budget",
                "Team collaboration",
                "Advanced analytics",
                "SLA guarantees",
                "On-premise deployment"
            ],
            "models": ["gpt-4", "gpt-3.5-turbo", "claude-3-opus", "claude-3-sonnet", "gemini-pro", "custom"]
        }
    ]
    
    for plan_data in plans_data:
        # Check if plan already exists
        existing = frappe.db.exists("AI Plan", plan_data["plan_id"])
        
        if existing:
            print(f"Plan '{plan_data['title']}' already exists, skipping...")
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
        
        # Add models
        for idx, model_name in enumerate(models, 1):
            plan.append("model_access", {
                "model_name": model_name,
                "idx": idx
            })
        
        plan.insert(ignore_permissions=True)
        print(f"✓ Created plan: {plan_data['title']}")
    
    frappe.db.commit()
    print("\n✓ All plans created successfully!")
    frappe.destroy()

if __name__ == "__main__":
    create_default_plans()
#!/usr/bin/env python3
"""
Create default AI Plans for Oropendola AI
Run this script to populate the database with pricing plans
"""

import frappe

def create_default_plans():
    """Create default AI subscription plans"""
    
    frappe.init(site='oropendola.ai')
    frappe.connect()
    frappe.set_user('Administrator')
    
    plans_data = [
        {
            "plan_id": "free-tier",
            "title": "Free Tier",
            "description": "Perfect for trying out Oropendola AI",
            "price": 0,
            "currency": "INR",
            "duration_days": 30,
            "requests_limit_per_day": 200,
            "monthly_budget_limit": 0,
            "support_level": "Community",
            "default_routing_mode": "cost_optimized",
            "is_active": 1,
            "features": [
                "200 requests/day",
                "5 AI models",
                "Standard support",
                "Auto routing mode"
            ],
            "models": ["gpt-3.5-turbo", "claude-3-haiku", "gemini-pro"]
        },
        {
            "plan_id": "pro-monthly",
            "title": "Pro Plan",
            "description": "For professional developers",
            "price": 1999,
            "currency": "INR",
            "duration_days": 30,
            "requests_limit_per_day": 5000,
            "monthly_budget_limit": 2000,
            "support_level": "Priority",
            "default_routing_mode": "balanced",
            "is_active": 1,
            "features": [
                "5000 requests/day",
                "All AI models",
                "Priority support",
                "Balanced routing",
                "₹2000 monthly budget",
                "Premium Fast Requests"
            ],
            "models": ["gpt-4", "gpt-3.5-turbo", "claude-3-sonnet", "claude-3-haiku", "gemini-pro"]
        },
        {
            "plan_id": "team-monthly",
            "title": "Team Plan",
            "description": "For development teams",
            "price": 9999,
            "currency": "INR",
            "duration_days": 30,
            "requests_limit_per_day": 25000,
            "monthly_budget_limit": 10000,
            "support_level": "Premium",
            "default_routing_mode": "performance",
            "is_active": 1,
            "features": [
                "25000 requests/day",
                "All AI models",
                "Premium support",
                "Performance routing",
                "₹10000 monthly budget",
                "Team collaboration",
                "Advanced analytics"
            ],
            "models": ["gpt-4", "gpt-3.5-turbo", "claude-3-opus", "claude-3-sonnet", "gemini-pro"]
        },
        {
            "plan_id": "corporate",
            "title": "Corporate",
            "description": "Custom enterprise solution",
            "price": 0,  # Custom pricing
            "currency": "INR",
            "duration_days": 365,
            "requests_limit_per_day": -1,  # Unlimited
            "monthly_budget_limit": 0,  # Custom
            "support_level": "Dedicated",
            "default_routing_mode": "performance",
            "is_active": 1,
            "features": [
                "Unlimited requests",
                "All AI models",
                "Dedicated support",
                "Custom routing",
                "Unlimited budget",
                "Team collaboration",
                "Advanced analytics",
                "SLA guarantees",
                "On-premise deployment"
            ],
            "models": ["gpt-4", "gpt-3.5-turbo", "claude-3-opus", "claude-3-sonnet", "gemini-pro", "custom"]
        }
    ]
    
    for plan_data in plans_data:
        # Check if plan already exists
        existing = frappe.db.exists("AI Plan", plan_data["plan_id"])
        
        if existing:
            print(f"Plan '{plan_data['title']}' already exists, skipping...")
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
        
        # Add models
        for idx, model_name in enumerate(models, 1):
            plan.append("model_access", {
                "model_name": model_name,
                "idx": idx
            })
        
        plan.insert(ignore_permissions=True)
        print(f"✓ Created plan: {plan_data['title']}")
    
    frappe.db.commit()
    print("\n✓ All plans created successfully!")
    frappe.destroy()

if __name__ == "__main__":
    create_default_plans()

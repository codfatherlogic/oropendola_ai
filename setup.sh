#!/bin/bash
# Oropendola AI - Quick Setup Script

set -e

echo "================================================"
echo "  Oropendola AI - Quick Setup"
echo "================================================"
echo ""

# Check if running in Frappe bench
if [ ! -f "sites/apps.txt" ]; then
    echo "❌ Error: This script must be run from frappe-bench directory"
    exit 1
fi

# Get site name
if [ -z "$1" ]; then
    echo "Usage: ./apps/oropendola_ai/setup.sh <site-name>"
    echo ""
    echo "Example: ./apps/oropendola_ai/setup.sh oropendola.local"
    exit 1
fi

SITE_NAME=$1

echo "📦 Setting up Oropendola AI for site: $SITE_NAME"
echo ""

# Step 1: Install dependencies
echo "1️⃣  Installing Python dependencies..."
pip install redis razorpay prometheus-client requests || {
    echo "⚠️  Warning: Some packages failed to install. Continuing..."
}

# Step 2: Migrate database
echo ""
echo "2️⃣  Running database migrations..."
bench --site $SITE_NAME migrate

# Step 3: Create .env template if not exists
ENV_FILE="apps/oropendola_ai/.env"
if [ ! -f "$ENV_FILE" ]; then
    echo ""
    echo "3️⃣  Creating environment configuration..."
    cat > $ENV_FILE << 'EOF'
# Oropendola AI Environment Configuration
# Copy this file and fill in your credentials

# Redis
REDIS_URL=redis://localhost:6379/0

# Payment Gateways
DEFAULT_PAYMENT_GATEWAY=razorpay

# Razorpay (Get from: https://dashboard.razorpay.com/)
RAZORPAY_KEY_ID=rzp_test_xxxxxxxxxxxxx
RAZORPAY_KEY_SECRET=your_razorpay_secret
RAZORPAY_WEBHOOK_SECRET=your_webhook_secret

# PayU (Get from: https://payu.in/)
PAYU_MERCHANT_KEY=your_payu_merchant_key
PAYU_MERCHANT_SALT=your_payu_salt
PAYU_MODE=test

# Model Endpoints
DEEPSEEK_ENDPOINT=https://api.deepseek.com/v1/chat/completions
DEEPSEEK_API_KEY=your_deepseek_key

GROK_ENDPOINT=https://api.x.ai/v1/chat/completions
GROK_API_KEY=your_grok_key

CLAUDE_ENDPOINT=https://api.anthropic.com/v1/messages
CLAUDE_API_KEY=your_claude_key

# Routing Weights
WEIGHT_LATENCY=1.0
WEIGHT_CAPACITY=0.5
WEIGHT_COST=1.5
WEIGHT_PRIORITY=2.0
EOF
    echo "✅ Created .env template at: $ENV_FILE"
    echo "   Please edit this file with your credentials"
else
    echo ""
    echo "3️⃣  Environment file already exists: $ENV_FILE"
fi

# Step 4: Enable scheduler
echo ""
echo "4️⃣  Enabling scheduler..."
bench --site $SITE_NAME scheduler enable

# Step 5: Create initialization script
INIT_SCRIPT="apps/oropendola_ai/init_data.py"
cat > $INIT_SCRIPT << 'PYEOF'
#!/usr/bin/env python3
"""Initialize default plans and models for Oropendola AI"""

import frappe

def create_default_plans():
    """Create default subscription plans"""
    
    plans = [
        {
            "plan_id": "PLAN-A-TRIAL",
            "title": "1-Day Trial",
            "description": "Perfect for testing our AI services",
            "price": 199,
            "currency": "INR",
            "duration_days": 1,
            "requests_limit_per_day": 200,
            "rate_limit_qps": 10,
            "priority_score": 10,
            "is_trial": 1,
            "is_active": 1,
            "support_level": "Standard",
            "features": [
                {"feature_name": "Premium Fast Requests", "enabled": 1}
            ],
            "model_access": [
                {"model_name": "DeepSeek", "is_allowed": 1, "cost_weight": 0.8},
                {"model_name": "Grok", "is_allowed": 1, "cost_weight": 0.6},
                {"model_name": "Claude", "is_allowed": 1, "cost_weight": 0.4}
            ]
        },
        {
            "plan_id": "PLAN-B-15DAYS",
            "title": "15-Day Standard",
            "description": "Great for regular users",
            "price": 999,
            "currency": "INR",
            "duration_days": 15,
            "requests_limit_per_day": 600,
            "rate_limit_qps": 20,
            "priority_score": 20,
            "is_trial": 0,
            "is_active": 1,
            "support_level": "Priority",
            "features": [
                {"feature_name": "Premium Fast Requests", "enabled": 1}
            ],
            "model_access": [
                {"model_name": "DeepSeek", "is_allowed": 1, "cost_weight": 0.8},
                {"model_name": "Grok", "is_allowed": 1, "cost_weight": 0.7},
                {"model_name": "Claude", "is_allowed": 1, "cost_weight": 0.6}
            ]
        },
        {
            "plan_id": "PLAN-C-UNLIMITED",
            "title": "1-Month Unlimited",
            "description": "Best for power users and enterprises",
            "price": 4999,
            "currency": "INR",
            "duration_days": 30,
            "requests_limit_per_day": -1,  # Unlimited
            "rate_limit_qps": 0,  # No limit
            "priority_score": 50,
            "is_trial": 0,
            "is_active": 1,
            "support_level": "Enterprise",
            "context_window_size": 1000000,
            "features": [
                {"feature_name": "Premium Fast Requests", "enabled": 1},
                {"feature_name": "High-Priority Support", "enabled": 1},
                {"feature_name": "Smart To-Do List", "enabled": 1},
                {"feature_name": "1M Context Window", "enabled": 1},
                {"feature_name": "Priority Queue", "enabled": 1}
            ],
            "model_access": [
                {"model_name": "DeepSeek", "is_allowed": 1, "cost_weight": 1.0},
                {"model_name": "Grok", "is_allowed": 1, "cost_weight": 1.0},
                {"model_name": "Claude", "is_allowed": 1, "cost_weight": 1.0}
            ]
        }
    ]
    
    for plan_data in plans:
        if not frappe.db.exists("AI Plan", plan_data["plan_id"]):
            plan = frappe.get_doc({
                "doctype": "AI Plan",
                **plan_data
            })
            plan.insert(ignore_permissions=True)
            print(f"✅ Created plan: {plan.title}")
        else:
            print(f"⏭️  Plan already exists: {plan_data['plan_id']}")
    
    frappe.db.commit()
    print("\n✨ Default plans created successfully!")

def create_default_models():
    """Create default AI model profiles"""
    
    models = [
        {
            "model_name": "DeepSeek",
            "provider": "DeepSeek AI",
            "endpoint_url": "https://api.deepseek.com/v1/chat/completions",
            "api_key_env_var": "DEEPSEEK_API_KEY",
            "capacity_score": 80,
            "cost_per_unit": 0.04,
            "is_active": 1,
            "health_status": "Up",
            "avg_latency_ms": 200,
            "max_context_window": 128000,
            "timeout_seconds": 30,
            "max_concurrent_requests": 20,
            "retry_attempts": 3,
            "tags": '["fast", "cost-effective"]'
        },
        {
            "model_name": "Grok",
            "provider": "X.AI",
            "endpoint_url": "https://api.x.ai/v1/chat/completions",
            "api_key_env_var": "GROK_API_KEY",
            "capacity_score": 90,
            "cost_per_unit": 0.03,
            "is_active": 1,
            "health_status": "Up",
            "avg_latency_ms": 250,
            "max_context_window": 128000,
            "timeout_seconds": 30,
            "max_concurrent_requests": 25,
            "retry_attempts": 3,
            "tags": '["high-quality", "reliable"]'
        },
        {
            "model_name": "Claude",
            "provider": "Anthropic",
            "endpoint_url": "https://api.anthropic.com/v1/messages",
            "api_key_env_var": "CLAUDE_API_KEY",
            "capacity_score": 85,
            "cost_per_unit": 0.02,
            "is_active": 1,
            "health_status": "Up",
            "avg_latency_ms": 300,
            "max_context_window": 200000,
            "timeout_seconds": 45,
            "max_concurrent_requests": 15,
            "retry_attempts": 3,
            "tags": '["best-quality", "large-context"]'
        }
    ]
    
    for model_data in models:
        if not frappe.db.exists("AI Model Profile", model_data["model_name"]):
            model = frappe.get_doc({
                "doctype": "AI Model Profile",
                **model_data
            })
            model.insert(ignore_permissions=True)
            print(f"✅ Created model: {model.model_name}")
        else:
            print(f"⏭️  Model already exists: {model_data['model_name']}")
    
    frappe.db.commit()
    print("\n✨ Default models created successfully!")

if __name__ == "__main__":
    frappe.init(site="{{SITE_NAME}}")
    frappe.connect()
    
    print("=" * 50)
    print("  Initializing Oropendola AI Data")
    print("=" * 50)
    print("")
    
    print("Creating default subscription plans...")
    create_default_plans()
    
    print("\nCreating default AI model profiles...")
    create_default_models()
    
    print("\n" + "=" * 50)
    print("  ✅ Initialization Complete!")
    print("=" * 50)
PYEOF

# Replace site name in init script
sed -i "s/{{SITE_NAME}}/$SITE_NAME/g" $INIT_SCRIPT
chmod +x $INIT_SCRIPT

# Step 6: Run initialization
echo ""
echo "5️⃣  Initializing default data (plans and models)..."
python3 $INIT_SCRIPT

# Step 7: Summary
echo ""
echo "================================================"
echo "  ✅ Setup Complete!"
echo "================================================"
echo ""
echo "📋 Next Steps:"
echo ""
echo "1. Edit environment file:"
echo "   nano apps/oropendola_ai/.env"
echo ""
echo "2. Configure payment gateways (Razorpay/PayU)"
echo "   See: apps/oropendola_ai/PAYMENT_GATEWAY_SETUP.md"
echo ""
echo "3. Start services:"
echo "   bench start"
echo ""
echo "4. In separate terminals:"
echo "   bench --site $SITE_NAME worker --queue short,default,long"
echo "   bench --site $SITE_NAME schedule"
echo ""
echo "5. Access your site:"
echo "   http://localhost:8000"
echo ""
echo "📚 Documentation:"
echo "   - Architecture: apps/oropendola_ai/ARCHITECTURE.md"
echo "   - Payment Setup: apps/oropendola_ai/PAYMENT_GATEWAY_SETUP.md"
echo "   - Complete Guide: apps/oropendola_ai/README_COMPLETE.md"
echo ""
echo "🎉 Happy coding!"
echo ""
#!/bin/bash
# Oropendola AI - Quick Setup Script

set -e

echo "================================================"
echo "  Oropendola AI - Quick Setup"
echo "================================================"
echo ""

# Check if running in Frappe bench
if [ ! -f "sites/apps.txt" ]; then
    echo "❌ Error: This script must be run from frappe-bench directory"
    exit 1
fi

# Get site name
if [ -z "$1" ]; then
    echo "Usage: ./apps/oropendola_ai/setup.sh <site-name>"
    echo ""
    echo "Example: ./apps/oropendola_ai/setup.sh oropendola.local"
    exit 1
fi

SITE_NAME=$1

echo "📦 Setting up Oropendola AI for site: $SITE_NAME"
echo ""

# Step 1: Install dependencies
echo "1️⃣  Installing Python dependencies..."
pip install redis razorpay prometheus-client requests || {
    echo "⚠️  Warning: Some packages failed to install. Continuing..."
}

# Step 2: Migrate database
echo ""
echo "2️⃣  Running database migrations..."
bench --site $SITE_NAME migrate

# Step 3: Create .env template if not exists
ENV_FILE="apps/oropendola_ai/.env"
if [ ! -f "$ENV_FILE" ]; then
    echo ""
    echo "3️⃣  Creating environment configuration..."
    cat > $ENV_FILE << 'EOF'
# Oropendola AI Environment Configuration
# Copy this file and fill in your credentials

# Redis
REDIS_URL=redis://localhost:6379/0

# Payment Gateways
DEFAULT_PAYMENT_GATEWAY=razorpay

# Razorpay (Get from: https://dashboard.razorpay.com/)
RAZORPAY_KEY_ID=rzp_test_xxxxxxxxxxxxx
RAZORPAY_KEY_SECRET=your_razorpay_secret
RAZORPAY_WEBHOOK_SECRET=your_webhook_secret

# PayU (Get from: https://payu.in/)
PAYU_MERCHANT_KEY=your_payu_merchant_key
PAYU_MERCHANT_SALT=your_payu_salt
PAYU_MODE=test

# Model Endpoints
DEEPSEEK_ENDPOINT=https://api.deepseek.com/v1/chat/completions
DEEPSEEK_API_KEY=your_deepseek_key

GROK_ENDPOINT=https://api.x.ai/v1/chat/completions
GROK_API_KEY=your_grok_key

CLAUDE_ENDPOINT=https://api.anthropic.com/v1/messages
CLAUDE_API_KEY=your_claude_key

# Routing Weights
WEIGHT_LATENCY=1.0
WEIGHT_CAPACITY=0.5
WEIGHT_COST=1.5
WEIGHT_PRIORITY=2.0
EOF
    echo "✅ Created .env template at: $ENV_FILE"
    echo "   Please edit this file with your credentials"
else
    echo ""
    echo "3️⃣  Environment file already exists: $ENV_FILE"
fi

# Step 4: Enable scheduler
echo ""
echo "4️⃣  Enabling scheduler..."
bench --site $SITE_NAME scheduler enable

# Step 5: Create initialization script
INIT_SCRIPT="apps/oropendola_ai/init_data.py"
cat > $INIT_SCRIPT << 'PYEOF'
#!/usr/bin/env python3
"""Initialize default plans and models for Oropendola AI"""

import frappe

def create_default_plans():
    """Create default subscription plans"""
    
    plans = [
        {
            "plan_id": "PLAN-A-TRIAL",
            "title": "1-Day Trial",
            "description": "Perfect for testing our AI services",
            "price": 199,
            "currency": "INR",
            "duration_days": 1,
            "requests_limit_per_day": 200,
            "rate_limit_qps": 10,
            "priority_score": 10,
            "is_trial": 1,
            "is_active": 1,
            "support_level": "Standard",
            "features": [
                {"feature_name": "Premium Fast Requests", "enabled": 1}
            ],
            "model_access": [
                {"model_name": "DeepSeek", "is_allowed": 1, "cost_weight": 0.8},
                {"model_name": "Grok", "is_allowed": 1, "cost_weight": 0.6},
                {"model_name": "Claude", "is_allowed": 1, "cost_weight": 0.4}
            ]
        },
        {
            "plan_id": "PLAN-B-15DAYS",
            "title": "15-Day Standard",
            "description": "Great for regular users",
            "price": 999,
            "currency": "INR",
            "duration_days": 15,
            "requests_limit_per_day": 600,
            "rate_limit_qps": 20,
            "priority_score": 20,
            "is_trial": 0,
            "is_active": 1,
            "support_level": "Priority",
            "features": [
                {"feature_name": "Premium Fast Requests", "enabled": 1}
            ],
            "model_access": [
                {"model_name": "DeepSeek", "is_allowed": 1, "cost_weight": 0.8},
                {"model_name": "Grok", "is_allowed": 1, "cost_weight": 0.7},
                {"model_name": "Claude", "is_allowed": 1, "cost_weight": 0.6}
            ]
        },
        {
            "plan_id": "PLAN-C-UNLIMITED",
            "title": "1-Month Unlimited",
            "description": "Best for power users and enterprises",
            "price": 4999,
            "currency": "INR",
            "duration_days": 30,
            "requests_limit_per_day": -1,  # Unlimited
            "rate_limit_qps": 0,  # No limit
            "priority_score": 50,
            "is_trial": 0,
            "is_active": 1,
            "support_level": "Enterprise",
            "context_window_size": 1000000,
            "features": [
                {"feature_name": "Premium Fast Requests", "enabled": 1},
                {"feature_name": "High-Priority Support", "enabled": 1},
                {"feature_name": "Smart To-Do List", "enabled": 1},
                {"feature_name": "1M Context Window", "enabled": 1},
                {"feature_name": "Priority Queue", "enabled": 1}
            ],
            "model_access": [
                {"model_name": "DeepSeek", "is_allowed": 1, "cost_weight": 1.0},
                {"model_name": "Grok", "is_allowed": 1, "cost_weight": 1.0},
                {"model_name": "Claude", "is_allowed": 1, "cost_weight": 1.0}
            ]
        }
    ]
    
    for plan_data in plans:
        if not frappe.db.exists("AI Plan", plan_data["plan_id"]):
            plan = frappe.get_doc({
                "doctype": "AI Plan",
                **plan_data
            })
            plan.insert(ignore_permissions=True)
            print(f"✅ Created plan: {plan.title}")
        else:
            print(f"⏭️  Plan already exists: {plan_data['plan_id']}")
    
    frappe.db.commit()
    print("\n✨ Default plans created successfully!")

def create_default_models():
    """Create default AI model profiles"""
    
    models = [
        {
            "model_name": "DeepSeek",
            "provider": "DeepSeek AI",
            "endpoint_url": "https://api.deepseek.com/v1/chat/completions",
            "api_key_env_var": "DEEPSEEK_API_KEY",
            "capacity_score": 80,
            "cost_per_unit": 0.04,
            "is_active": 1,
            "health_status": "Up",
            "avg_latency_ms": 200,
            "max_context_window": 128000,
            "timeout_seconds": 30,
            "max_concurrent_requests": 20,
            "retry_attempts": 3,
            "tags": '["fast", "cost-effective"]'
        },
        {
            "model_name": "Grok",
            "provider": "X.AI",
            "endpoint_url": "https://api.x.ai/v1/chat/completions",
            "api_key_env_var": "GROK_API_KEY",
            "capacity_score": 90,
            "cost_per_unit": 0.03,
            "is_active": 1,
            "health_status": "Up",
            "avg_latency_ms": 250,
            "max_context_window": 128000,
            "timeout_seconds": 30,
            "max_concurrent_requests": 25,
            "retry_attempts": 3,
            "tags": '["high-quality", "reliable"]'
        },
        {
            "model_name": "Claude",
            "provider": "Anthropic",
            "endpoint_url": "https://api.anthropic.com/v1/messages",
            "api_key_env_var": "CLAUDE_API_KEY",
            "capacity_score": 85,
            "cost_per_unit": 0.02,
            "is_active": 1,
            "health_status": "Up",
            "avg_latency_ms": 300,
            "max_context_window": 200000,
            "timeout_seconds": 45,
            "max_concurrent_requests": 15,
            "retry_attempts": 3,
            "tags": '["best-quality", "large-context"]'
        }
    ]
    
    for model_data in models:
        if not frappe.db.exists("AI Model Profile", model_data["model_name"]):
            model = frappe.get_doc({
                "doctype": "AI Model Profile",
                **model_data
            })
            model.insert(ignore_permissions=True)
            print(f"✅ Created model: {model.model_name}")
        else:
            print(f"⏭️  Model already exists: {model_data['model_name']}")
    
    frappe.db.commit()
    print("\n✨ Default models created successfully!")

if __name__ == "__main__":
    frappe.init(site="{{SITE_NAME}}")
    frappe.connect()
    
    print("=" * 50)
    print("  Initializing Oropendola AI Data")
    print("=" * 50)
    print("")
    
    print("Creating default subscription plans...")
    create_default_plans()
    
    print("\nCreating default AI model profiles...")
    create_default_models()
    
    print("\n" + "=" * 50)
    print("  ✅ Initialization Complete!")
    print("=" * 50)
PYEOF

# Replace site name in init script
sed -i "s/{{SITE_NAME}}/$SITE_NAME/g" $INIT_SCRIPT
chmod +x $INIT_SCRIPT

# Step 6: Run initialization
echo ""
echo "5️⃣  Initializing default data (plans and models)..."
python3 $INIT_SCRIPT

# Step 7: Summary
echo ""
echo "================================================"
echo "  ✅ Setup Complete!"
echo "================================================"
echo ""
echo "📋 Next Steps:"
echo ""
echo "1. Edit environment file:"
echo "   nano apps/oropendola_ai/.env"
echo ""
echo "2. Configure payment gateways (Razorpay/PayU)"
echo "   See: apps/oropendola_ai/PAYMENT_GATEWAY_SETUP.md"
echo ""
echo "3. Start services:"
echo "   bench start"
echo ""
echo "4. In separate terminals:"
echo "   bench --site $SITE_NAME worker --queue short,default,long"
echo "   bench --site $SITE_NAME schedule"
echo ""
echo "5. Access your site:"
echo "   http://localhost:8000"
echo ""
echo "📚 Documentation:"
echo "   - Architecture: apps/oropendola_ai/ARCHITECTURE.md"
echo "   - Payment Setup: apps/oropendola_ai/PAYMENT_GATEWAY_SETUP.md"
echo "   - Complete Guide: apps/oropendola_ai/README_COMPLETE.md"
echo ""
echo "🎉 Happy coding!"
echo ""

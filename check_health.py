#!/usr/bin/env python3
"""
Quick diagnostic script to check AI Model Profile health status
"""

import frappe

def check_models():
    frappe.init(site='oropendola.ai')
    frappe.connect()
    
    models = frappe.get_all('AI Model Profile', fields=['*'])
    
    print("\n" + "="*80)
    print("AI MODEL PROFILE HEALTH STATUS")
    print("="*80 + "\n")
    
    for model in models:
        print(f"📊 {model.model_name} ({model.name})")
        print(f"   Status: {model.health_status}")
        print(f"   Endpoint: {model.endpoint_url}")

        # Generate config key from model name
        config_key = f"{model.model_name.lower().replace(' ', '_')}_api_key"
        print(f"   Config Key: {config_key}")
        print(f"   Last Check: {model.last_health_check or 'Never'}")

        # Check if API key exists in site config
        api_key = frappe.conf.get(config_key)
        if api_key:
            print(f"   ✅ API Key Configured: {api_key[:10]}...")
        else:
            print(f"   ❌ API Key NOT Configured in site config")

        print()
    
    print("="*80)
    print("\n💡 To configure API keys:")
    print("   Option 1: Via AI Model Profile UI (Recommended)")
    print("      - Go to AI Model Profile")
    print("      - Edit the model")
    print("      - Enter API key in the 'API Key' field")
    print("      - Save (key is automatically saved to site config)")
    print()
    print("   Option 2: Via command line")
    print("      bench --site oropendola.ai set-config deepseek_api_key 'sk-...'")
    print("      bench --site oropendola.ai set-config grok_api_key 'xai-...'")
    print("      bench --site oropendola.ai set-config claude_api_key 'sk-ant-...'")
    print()
    print("   Then run health check:")
    print("      bench --site oropendola.ai execute oropendola_ai.oropendola_ai.tasks.perform_health_checks")
    print()
    
    frappe.destroy()

if __name__ == '__main__':
    check_models()

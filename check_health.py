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
        print(f"   API Key Env: {model.api_key_env_var}")
        print(f"   Last Check: {model.last_health_check or 'Never'}")
        
        # Check if API key exists
        api_key = frappe.conf.get(model.api_key_env_var) if model.api_key_env_var else None
        if api_key:
            print(f"   ✅ API Key Configured: {api_key[:10]}...")
        else:
            print(f"   ❌ API Key NOT Configured")
        
        print()
    
    print("="*80)
    print("\n💡 To fix 'Down' status:")
    print("   1. Configure API keys in site config:")
    print("      bench --site oropendola.ai set-config OPENAI_API_KEY 'sk-...'")
    print("   2. Run health check:")
    print("      bench --site oropendola.ai execute oropendola_ai.oropendola_ai.tasks.perform_health_checks")
    print()
    
    frappe.destroy()

if __name__ == '__main__':
    check_models()

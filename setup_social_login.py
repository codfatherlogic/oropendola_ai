#!/usr/bin/env python3
"""
Setup script to create sample Social Login Key records for testing
"""

import sys
import os

# Add the frappe app to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../'))

import frappe

def setup_social_login():
    """Create sample social login providers"""
    frappe.init('oropendola.ai')
    frappe.connect()
    
    try:
        # Define providers to create
        providers = [
            {
                'provider': 'google',
                'client_id': 'your_google_client_id',
                'client_secret': 'your_google_client_secret',
                'enabled': 1
            },
            {
                'provider': 'github',
                'client_id': 'your_github_client_id',
                'client_secret': 'your_github_client_secret',
                'enabled': 1
            }
        ]
        
        for provider_data in providers:
            # Check if provider already exists
            existing = frappe.db.get_value('Social Login Key', 
                                         {'provider': provider_data['provider']})
            
            if existing:
                print(f"✅ {provider_data['provider'].capitalize()} social login already exists")
                continue
            
            # Create new Social Login Key
            social_login = frappe.new_doc('Social Login Key')
            social_login.update(provider_data)
            social_login.insert(ignore_permissions=True)
            frappe.db.commit()
            print(f"✅ Created {provider_data['provider'].capitalize()} social login")
        
        print("\n✅ Social login setup complete!")
        print("⚠️  Note: Update the client_id and client_secret with actual OAuth credentials\n")
        
    except Exception as e:
        print(f"❌ Error setting up social login: {str(e)}")
        frappe.db.rollback()
    finally:
        frappe.destroy()

if __name__ == '__main__':
    setup_social_login()

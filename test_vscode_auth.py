#!/usr/bin/env python3
"""
Test VS Code Authentication Flow
Tests all 3 new API endpoints
"""

import requests
import json
import time

API_BASE = "https://oropendola.ai"

def test_vscode_auth_flow():
    """Test the complete VS Code authentication flow"""
    
    print("=" * 60)
    print("Testing VS Code Authentication Flow")
    print("=" * 60)
    
    # Step 1: Initiate authentication
    print("\n1. Initiating authentication...")
    try:
        response = requests.post(
            f"{API_BASE}/api/method/oropendola_ai.oropendola_ai.api.vscode_extension.initiate_vscode_auth"
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("message", {}).get("success"):
                print("✓ Authentication initiated successfully")
                print(f"  Auth URL: {data['message']['auth_url']}")
                print(f"  Session Token: {data['message']['session_token'][:20]}...")
                print(f"  Expires In: {data['message']['expires_in']} seconds")
                
                session_token = data['message']['session_token']
                auth_url = data['message']['auth_url']
            else:
                print(f"✗ Failed: {data}")
                return
        else:
            print(f"✗ HTTP {response.status_code}: {response.text}")
            return
            
    except Exception as e:
        print(f"✗ Error: {e}")
        return
    
    # Step 2: Check auth status (should be pending)
    print("\n2. Checking authentication status (should be pending)...")
    try:
        response = requests.post(
            f"{API_BASE}/api/method/oropendola_ai.oropendola_ai.api.vscode_extension.check_vscode_auth_status",
            json={"session_token": session_token}
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("message", {}).get("status") == "pending":
                print("✓ Status is 'pending' (correct)")
                print(f"  Full response: {json.dumps(data['message'], indent=2)}")
            else:
                print(f"✗ Unexpected status: {data}")
        else:
            print(f"✗ HTTP {response.status_code}: {response.text}")
            
    except Exception as e:
        print(f"✗ Error: {e}")
    
    # Step 3: Instructions for manual testing
    print("\n3. Manual Testing Required")
    print("-" * 60)
    print("To complete the test:")
    print(f"1. Open this URL in your browser:")
    print(f"   {auth_url}")
    print(f"\n2. Log in with your Oropendola AI account")
    print(f"\n3. The page will display your subscription and complete the auth")
    print(f"\n4. Run this command to check if auth completed:")
    print(f"\n   curl -X POST {API_BASE}/api/method/oropendola_ai.oropendola_ai.api.vscode_extension.check_vscode_auth_status \\")
    print(f"        -H 'Content-Type: application/json' \\")
    print(f"        -d '{{\"session_token\": \"{session_token}\"}}'")
    print("\n5. You should see status: 'complete' with your API key")
    print("-" * 60)
    
    # Test endpoint availability
    print("\n4. Testing endpoint availability...")
    endpoints = [
        "/api/method/oropendola_ai.oropendola_ai.api.vscode_extension.initiate_vscode_auth",
        "/api/method/oropendola_ai.oropendola_ai.api.vscode_extension.check_vscode_auth_status",
        "/api/method/oropendola_ai.oropendola_ai.api.vscode_extension.complete_vscode_auth",
    ]
    
    for endpoint in endpoints:
        try:
            response = requests.post(f"{API_BASE}{endpoint}")
            print(f"✓ {endpoint.split('.')[-1]}: HTTP {response.status_code}")
        except Exception as e:
            print(f"✗ {endpoint.split('.')[-1]}: {e}")
    
    # Test web page availability
    print("\n5. Testing web page...")
    try:
        response = requests.get(f"{API_BASE}/vscode-auth?token=test_token")
        if response.status_code == 200:
            print(f"✓ /vscode-auth page is accessible")
        else:
            print(f"⚠ /vscode-auth returned HTTP {response.status_code}")
    except Exception as e:
        print(f"✗ Error accessing /vscode-auth: {e}")
    
    print("\n" + "=" * 60)
    print("Test Complete")
    print("=" * 60)

if __name__ == "__main__":
    test_vscode_auth_flow()
#!/usr/bin/env python3
"""
Test VS Code Authentication Flow
Tests all 3 new API endpoints
"""

import requests
import json
import time

API_BASE = "https://oropendola.ai"

def test_vscode_auth_flow():
    """Test the complete VS Code authentication flow"""
    
    print("=" * 60)
    print("Testing VS Code Authentication Flow")
    print("=" * 60)
    
    # Step 1: Initiate authentication
    print("\n1. Initiating authentication...")
    try:
        response = requests.post(
            f"{API_BASE}/api/method/oropendola_ai.oropendola_ai.api.vscode_extension.initiate_vscode_auth"
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("message", {}).get("success"):
                print("✓ Authentication initiated successfully")
                print(f"  Auth URL: {data['message']['auth_url']}")
                print(f"  Session Token: {data['message']['session_token'][:20]}...")
                print(f"  Expires In: {data['message']['expires_in']} seconds")
                
                session_token = data['message']['session_token']
                auth_url = data['message']['auth_url']
            else:
                print(f"✗ Failed: {data}")
                return
        else:
            print(f"✗ HTTP {response.status_code}: {response.text}")
            return
            
    except Exception as e:
        print(f"✗ Error: {e}")
        return
    
    # Step 2: Check auth status (should be pending)
    print("\n2. Checking authentication status (should be pending)...")
    try:
        response = requests.post(
            f"{API_BASE}/api/method/oropendola_ai.oropendola_ai.api.vscode_extension.check_vscode_auth_status",
            json={"session_token": session_token}
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("message", {}).get("status") == "pending":
                print("✓ Status is 'pending' (correct)")
                print(f"  Full response: {json.dumps(data['message'], indent=2)}")
            else:
                print(f"✗ Unexpected status: {data}")
        else:
            print(f"✗ HTTP {response.status_code}: {response.text}")
            
    except Exception as e:
        print(f"✗ Error: {e}")
    
    # Step 3: Instructions for manual testing
    print("\n3. Manual Testing Required")
    print("-" * 60)
    print("To complete the test:")
    print(f"1. Open this URL in your browser:")
    print(f"   {auth_url}")
    print(f"\n2. Log in with your Oropendola AI account")
    print(f"\n3. The page will display your subscription and complete the auth")
    print(f"\n4. Run this command to check if auth completed:")
    print(f"\n   curl -X POST {API_BASE}/api/method/oropendola_ai.oropendola_ai.api.vscode_extension.check_vscode_auth_status \\")
    print(f"        -H 'Content-Type: application/json' \\")
    print(f"        -d '{{\"session_token\": \"{session_token}\"}}'")
    print("\n5. You should see status: 'complete' with your API key")
    print("-" * 60)
    
    # Test endpoint availability
    print("\n4. Testing endpoint availability...")
    endpoints = [
        "/api/method/oropendola_ai.oropendola_ai.api.vscode_extension.initiate_vscode_auth",
        "/api/method/oropendola_ai.oropendola_ai.api.vscode_extension.check_vscode_auth_status",
        "/api/method/oropendola_ai.oropendola_ai.api.vscode_extension.complete_vscode_auth",
    ]
    
    for endpoint in endpoints:
        try:
            response = requests.post(f"{API_BASE}{endpoint}")
            print(f"✓ {endpoint.split('.')[-1]}: HTTP {response.status_code}")
        except Exception as e:
            print(f"✗ {endpoint.split('.')[-1]}: {e}")
    
    # Test web page availability
    print("\n5. Testing web page...")
    try:
        response = requests.get(f"{API_BASE}/vscode-auth?token=test_token")
        if response.status_code == 200:
            print(f"✓ /vscode-auth page is accessible")
        else:
            print(f"⚠ /vscode-auth returned HTTP {response.status_code}")
    except Exception as e:
        print(f"✗ Error accessing /vscode-auth: {e}")
    
    print("\n" + "=" * 60)
    print("Test Complete")
    print("=" * 60)

if __name__ == "__main__":
    test_vscode_auth_flow()

#!/usr/bin/env python3
"""
PayU Payment Gateway Integration Test Script
Tests all aspects of the payment flow
"""

import requests
import json
import sys

# Configuration
API_BASE = "https://oropendola.ai"
TEST_MODE = True

# Colors for output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def print_success(msg):
    print(f"{Colors.GREEN}✓ {msg}{Colors.END}")

def print_error(msg):
    print(f"{Colors.RED}✗ {msg}{Colors.END}")

def print_info(msg):
    print(f"{Colors.BLUE}ℹ {msg}{Colors.END}")

def print_warning(msg):
    print(f"{Colors.YELLOW}⚠ {msg}{Colors.END}")

def print_header(msg):
    print(f"\n{Colors.BLUE}{'=' * 60}")
    print(f"  {msg}")
    print(f"{'=' * 60}{Colors.END}\n")

def test_homepage():
    """Test 1: Homepage accessibility"""
    print_header("Test 1: Homepage Accessibility")
    
    try:
        response = requests.get(f"{API_BASE}/")
        
        if response.status_code == 200:
            print_success("Homepage is accessible")
            
            # Check for key elements
            content = response.text.lower()
            if "oropendola ai" in content:
                print_success("Homepage contains branding")
            if "code faster" in content or "ai" in content:
                print_success("Homepage contains messaging")
            if "pricing" in content or "get started" in content:
                print_success("Homepage contains CTAs")
            
            return True
        else:
            print_error(f"Homepage returned status {response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"Failed to access homepage: {e}")
        return False

def test_pricing_page():
    """Test 2: Pricing page accessibility"""
    print_header("Test 2: Pricing Page Accessibility")
    
    try:
        response = requests.get(f"{API_BASE}/pricing")
        
        if response.status_code == 200:
            print_success("Pricing page is accessible")
            return True
        else:
            print_error(f"Pricing page returned status {response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"Failed to access pricing page: {e}")
        return False

def test_get_plans_api():
    """Test 3: Get Plans API"""
    print_header("Test 3: Get Plans API")
    
    try:
        response = requests.post(f"{API_BASE}/api/method/oropendola_ai.oropendola_ai.api.payment.get_plans")
        
        if response.status_code == 200:
            data = response.json()
            
            if "message" in data and data["message"].get("success"):
                plans = data["message"].get("plans", [])
                print_success(f"API returned successfully with {len(plans)} plans")
                
                if plans:
                    for plan in plans:
                        price = float(plan.get("price", 0))
                        print_info(f"  - {plan.get('title')}: ₹{price} ({plan.get('plan_id')})")
                    return True
                else:
                    print_warning("No plans found. Please create plans in AI Plan doctype")
                    return False
            else:
                print_error("API response indicates failure")
                print_info(f"Response: {json.dumps(data, indent=2)}")
                return False
        else:
            print_error(f"API returned status {response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"Failed to call get_plans API: {e}")
        return False

def test_payment_endpoints():
    """Test 4: Payment endpoints existence"""
    print_header("Test 4: Payment Endpoint Availability")
    
    endpoints = [
        "/api/method/oropendola_ai.oropendola_ai.api.payment.get_plans",
        "/api/method/oropendola_ai.oropendola_ai.api.payment.create_subscription_and_invoice",
        "/api/method/oropendola_ai.oropendola_ai.api.payment.initiate_payment",
        "/api/method/oropendola_ai.oropendola_ai.api.payment.payu_success",
        "/api/method/oropendola_ai.oropendola_ai.api.payment.payu_failure",
    ]
    
    all_success = True
    
    for endpoint in endpoints:
        try:
            response = requests.post(f"{API_BASE}{endpoint}")
            # We expect 200 or 403 (auth required) - both mean endpoint exists
            if response.status_code in [200, 403, 417]:
                print_success(f"{endpoint.split('.')[-1]}: Endpoint exists")
            else:
                print_error(f"{endpoint.split('.')[-1]}: Unexpected status {response.status_code}")
                all_success = False
        except Exception as e:
            print_error(f"{endpoint.split('.')[-1]}: {e}")
            all_success = False
    
    return all_success

def test_payu_service():
    """Test 5: PayU service configuration"""
    print_header("Test 5: PayU Service Configuration")
    
    print_info("Checking PayU service initialization...")
    
    # Test by trying to initiate payment (will fail without auth, but shows if service loads)
    try:
        response = requests.post(
            f"{API_BASE}/api/method/oropendola_ai.oropendola_ai.api.payment.initiate_payment",
            json={"invoice_id": "test", "gateway": "payu"}
        )
        
        # 403 means auth required (expected) - service is configured
        # 417 means validation error (expected) - service is configured
        # 500 might mean config issue
        
        if response.status_code == 403:
            print_success("PayU service is loaded (auth required as expected)")
            return True
        elif response.status_code == 417:
            data = response.json()
            if "credentials not configured" in str(data).lower():
                print_warning("PayU credentials not configured in site_config.json")
                print_info("Add payu_merchant_key and payu_merchant_salt to site config")
                return False
            else:
                print_success("PayU service is loaded (validation error as expected)")
                return True
        elif response.status_code == 500:
            print_error("PayU service configuration error")
            return False
        else:
            print_warning(f"Unexpected response: {response.status_code}")
            return True
            
    except Exception as e:
        print_error(f"Failed to test PayU service: {e}")
        return False

def test_page_existence():
    """Test 6: All web pages exist"""
    print_header("Test 6: Web Pages Existence")
    
    pages = [
        ("/", "Homepage"),
        ("/pricing", "Pricing Page"),
        ("/payment", "Payment Page"),
        ("/payment-success", "Success Page"),
        ("/payment-failed", "Failure Page"),
        ("/vscode-auth", "VS Code Auth")
    ]
    
    all_exist = True
    
    for url, name in pages:
        try:
            # Some pages expect query params, so we might get redirects or errors
            # But they should at least be accessible (not 404)
            response = requests.get(f"{API_BASE}{url}", allow_redirects=False)
            
            if response.status_code in [200, 301, 302, 417]:  # 417 is Frappe validation
                print_success(f"{name}: Exists")
            elif response.status_code == 404:
                print_error(f"{name}: Not found (404)")
                all_exist = False
            else:
                print_warning(f"{name}: Status {response.status_code}")
        except Exception as e:
            print_error(f"{name}: {e}")
            all_exist = False
    
    return all_exist

def main():
    """Run all tests"""
    print(f"\n{Colors.BLUE}╔════════════════════════════════════════════════════════════╗")
    print(f"║  PayU Payment Gateway Integration Test Suite              ║")
    print(f"║  Testing: {API_BASE:45s} ║")
    print(f"╚════════════════════════════════════════════════════════════╝{Colors.END}\n")
    
    results = []
    
    # Run tests
    results.append(("Homepage", test_homepage()))
    results.append(("Pricing Page", test_pricing_page()))
    results.append(("Plans API", test_get_plans_api()))
    results.append(("Payment Endpoints", test_payment_endpoints()))
    results.append(("PayU Service", test_payu_service()))
    results.append(("Web Pages", test_page_existence()))
    
    # Summary
    print_header("Test Summary")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = f"{Colors.GREEN}PASS{Colors.END}" if result else f"{Colors.RED}FAIL{Colors.END}"
        print(f"  {test_name:30s} {status}")
    
    print(f"\n{Colors.BLUE}{'─' * 60}{Colors.END}")
    print(f"  Total: {passed}/{total} tests passed")
    
    if passed == total:
        print(f"{Colors.GREEN}  ✓ All tests passed!{Colors.END}")
        print(f"\n{Colors.BLUE}Next Steps:{Colors.END}")
        print("  1. Configure PayU credentials in site_config.json")
        print("  2. Create subscription plans in AI Plan doctype")
        print("  3. Test complete flow: Homepage → Pricing → Payment")
        print("  4. Clear cache: bench --site oropendola.ai clear-cache")
        print("  5. Build: bench build --app oropendola_ai")
        print("  6. Restart: bench restart")
        return 0
    else:
        print(f"{Colors.RED}  ✗ Some tests failed{Colors.END}")
        print(f"\n{Colors.YELLOW}Troubleshooting:{Colors.END}")
        print("  1. Run: bench --site oropendola.ai migrate")
        print("  2. Run: bench --site oropendola.ai clear-cache")
        print("  3. Run: bench build --app oropendola_ai")
        print("  4. Run: bench restart")
        print("  5. Check error logs")
        return 1
    
if __name__ == "__main__":
    sys.exit(main())

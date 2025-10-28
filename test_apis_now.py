#!/usr/bin/env python3
"""
Test the APIs after task restart
"""
import requests

backend_url = 'http://alertw-alb-1475356777.us-east-1.elb.amazonaws.com/api'

print("=" * 80)
print("TESTING BACKEND APIS AFTER TASK RESTART")
print("=" * 80)

test_endpoints = [
    ('/health', 'Health Check'),
    ('/alerts?company_id=company-demo&status=active', 'Get Alerts'),
    ('/incidents?company_id=company-demo', 'Get Incidents'),
]

all_passed = True

for endpoint, name in test_endpoints:
    url = f"{backend_url}{endpoint}"
    print(f"\n🧪 Testing: {name}")
    print(f"   URL: {url}")
    
    try:
        response = requests.get(url, timeout=10)
        status_code = response.status_code
        
        if status_code == 200:
            print(f"   ✅ Status: {status_code}")
            
            try:
                data = response.json()
                if isinstance(data, list):
                    print(f"   Response: List with {len(data)} items")
                    if len(data) > 0:
                        print(f"   First item keys: {list(data[0].keys())[:5]}")
                elif isinstance(data, dict):
                    print(f"   Response: {data}")
            except:
                print(f"   Response (text): {response.text[:200]}")
        else:
            print(f"   ❌ Status: {status_code}")
            print(f"   Response: {response.text[:500]}")
            all_passed = False
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        all_passed = False

print(f"\n" + "=" * 80)
if all_passed:
    print("✅ ALL TESTS PASSED!")
    print("The backend is now working correctly!")
else:
    print("❌ SOME TESTS FAILED")
    print("Still investigating the issue...")
print("=" * 80)

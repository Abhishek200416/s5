#!/usr/bin/env python3
"""
Check backend health and test API endpoints
"""
import requests
import json

# Backend ALB URL from problem statement
backend_urls = [
    "http://alert-whisperer-alb-728925775278.us-east-1.elb.amazonaws.com",
    "http://alert-whisperer-alb-728925775278.us-east-1.elb.amazonaws.com/api"
]

print("=" * 80)
print("TESTING BACKEND CONNECTIVITY")
print("=" * 80)

for base_url in backend_urls:
    print(f"\nTesting: {base_url}")
    print("-" * 80)
    
    # Test health endpoint
    try:
        health_url = f"{base_url}/health"
        print(f"GET {health_url}")
        response = requests.get(health_url, timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text[:200]}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test login endpoint
    try:
        login_url = f"{base_url}/login"
        print(f"\nPOST {login_url}")
        payload = {
            "email": "admin@alertwhisperer.com",
            "password": "admin123"
        }
        response = requests.post(login_url, json=payload, timeout=10)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print(f"✅ Login successful!")
            data = response.json()
            print(f"Token: {data.get('access_token', '')[:50]}...")
        else:
            print(f"Response: {response.text[:500]}")
    except Exception as e:
        print(f"❌ Error: {e}")

print("\n" + "=" * 80)

#!/usr/bin/env python3
"""
Test actual ALB endpoints
"""
import requests
import json

backends = [
    "http://alertw-alb-1475356777.us-east-1.elb.amazonaws.com",
    "http://alert-whisperer-alb-1592907964.us-east-1.elb.amazonaws.com"
]

for backend_url in backends:
    print("=" * 80)
    print(f"TESTING: {backend_url}")
    print("=" * 80)
    
    # Test health with and without /api prefix
    for path in ["/api/health", "/health"]:
        try:
            url = f"{backend_url}{path}"
            print(f"\nGET {url}")
            response = requests.get(url, timeout=10)
            print(f"✅ Status: {response.status_code}")
            print(f"Response: {response.text[:200]}")
            
            if response.status_code == 200:
                print(f"\n🎉 WORKING ENDPOINT FOUND: {url}")
                
                # Try login
                login_url = f"{backend_url}/api/login"
                print(f"\nTrying login at: {login_url}")
                payload = {
                    "email": "admin@alertwhisperer.com",
                    "password": "admin123"
                }
                login_response = requests.post(login_url, json=payload, timeout=10)
                print(f"Login Status: {login_response.status_code}")
                if login_response.status_code == 200:
                    print(f"✅ LOGIN SUCCESSFUL!")
                    data = login_response.json()
                    print(f"User: {data.get('user', {}).get('name', 'Unknown')}")
                else:
                    print(f"Login Response: {login_response.text[:500]}")
                
                break
        except Exception as e:
            print(f"❌ Error: {str(e)[:200]}")
    
    print()

#!/usr/bin/env python3
"""
Comprehensive login test after deployment
"""

import requests
import time
import sys

BACKEND_URL = "http://alertw-alb-1475356777.us-east-1.elb.amazonaws.com"

def test_login():
    """Test login endpoint"""
    print("\n🔐 Testing Login...")
    print(f"   Endpoint: {BACKEND_URL}/api/auth/login")
    print(f"   Email: admin@alertwhisperer.com")
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/api/auth/login",
            json={
                "email": "admin@alertwhisperer.com",
                "password": "admin123"
            },
            timeout=15
        )
        
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Login Successful!")
            print(f"   Response keys: {list(data.keys())}")
            
            if 'access_token' in data:
                print(f"   ✅ Access token received")
                return True, data
            else:
                print(f"   ⚠️  No access token in response")
                return False, data
        else:
            print(f"   ❌ Login Failed")
            print(f"   Response: {response.text[:500]}")
            return False, None
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False, None

def test_health():
    """Test various health endpoints"""
    endpoints = [
        "/api/health",
        "/health",
        "/api/companies",
        "/docs"
    ]
    
    print("\n🏥 Testing Backend Health...")
    for endpoint in endpoints:
        try:
            response = requests.get(f"{BACKEND_URL}{endpoint}", timeout=10)
            print(f"   {endpoint}: HTTP {response.status_code}")
            if response.status_code == 200:
                return True
        except Exception as e:
            print(f"   {endpoint}: Error - {e}")
    
    return False

if __name__ == '__main__':
    print("=" * 70)
    print("🚀 Alert Whisperer Login Test")
    print("=" * 70)
    
    # Wait a bit for deployment
    print("\n⏳ Waiting 60 seconds for deployment to stabilize...")
    time.sleep(60)
    
    # Test health first
    health_ok = test_health()
    
    # Test login
    success, data = test_login()
    
    print("\n" + "=" * 70)
    if success:
        print("🎉 SUCCESS! Login is working!")
        print("=" * 70)
        print("\n✅ Your Alert Whisperer app is ready!")
        print(f"\n🔗 Backend: {BACKEND_URL}")
        print("🔗 Frontend: http://alert-whisperer-frontend-728925775278.s3-website-us-east-1.amazonaws.com")
        print("\n🔐 Login Credentials:")
        print("   Email: admin@alertwhisperer.com")
        print("   Password: admin123")
        sys.exit(0)
    else:
        print("⚠️ Login still not working")
        print("=" * 70)
        print("\nTroubleshooting steps:")
        print("1. Wait another 2-3 minutes for deployment")
        print("2. Check ECS task logs")
        print("3. Verify DynamoDB tables have data")
        sys.exit(1)

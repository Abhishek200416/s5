#!/usr/bin/env python3
"""
Test script to verify DynamoDB migration is successful
"""
import requests
import json

BASE_URL = "http://localhost:8001/api"

def test_health():
    """Test health endpoint"""
    print("🔍 Testing health endpoint...")
    response = requests.get(f"{BASE_URL}/health")
    assert response.status_code == 200
    print(f"   ✅ Health check passed: {response.json()}")

def test_login():
    """Test login with DynamoDB"""
    print("\n🔍 Testing login endpoint...")
    response = requests.post(
        f"{BASE_URL}/auth/login",
        json={"email": "admin@alertwhisperer.com", "password": "admin123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "user" in data
    print(f"   ✅ Login successful!")
    print(f"   User: {data['user']['email']} ({data['user']['role']})")
    return data["access_token"]

def test_companies(token):
    """Test companies endpoint"""
    print("\n🔍 Testing companies endpoint...")
    response = requests.get(
        f"{BASE_URL}/companies",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    companies = response.json()
    print(f"   ✅ Found {len(companies)} companies")
    for company in companies[:3]:
        print(f"      - {company['name']}")

def test_profile(token):
    """Test profile endpoint"""
    print("\n🔍 Testing profile endpoint...")
    response = requests.get(
        f"{BASE_URL}/profile",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    profile = response.json()
    print(f"   ✅ Profile retrieved: {profile['name']}")

if __name__ == "__main__":
    print("="*70)
    print("  DynamoDB Migration Test Suite")
    print("="*70)
    
    try:
        test_health()
        token = test_login()
        test_companies(token)
        test_profile(token)
        
        print("\n" + "="*70)
        print("  ✅ ALL TESTS PASSED - DynamoDB Migration Successful!")
        print("="*70)
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        exit(1)

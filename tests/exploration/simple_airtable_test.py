#!/usr/bin/env python3
"""
Simple Airtable access test
"""

import os
import httpx
from dotenv import load_dotenv

def simple_test():
    """Simple test to see what we can access"""
    load_dotenv("../config/config.env")
    
    api_key = os.getenv("AIRTABLE_API_KEY")
    base_id = os.getenv("AIRTABLE_BASE_ID")
    
    print(f"🔍 Testing with:")
    print(f"   API Key: {api_key[:20]}...")
    print(f"   Base ID: {base_id}")
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # Test 1: Try to access the base directly
    print(f"\n📋 Test 1: Direct base access")
    try:
        url = f"https://api.airtable.com/v0/{base_id}"
        response = httpx.get(url, headers=headers)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print(f"   ✅ Success! Base accessible")
        else:
            print(f"   ❌ Error: {response.text[:200]}")
    except Exception as e:
        print(f"   ❌ Exception: {e}")
    
    # Test 2: Try to list tables (different endpoint)
    print(f"\n📋 Test 2: List tables endpoint")
    try:
        url = f"https://api.airtable.com/v0/{base_id}/tables"
        response = httpx.get(url, headers=headers)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print(f"   ✅ Success! Tables accessible")
            data = response.json()
            print(f"   Tables: {data}")
        else:
            print(f"   ❌ Error: {response.text[:200]}")
    except Exception as e:
        print(f"   ❌ Exception: {e}")
    
    # Test 3: Try to get user info
    print(f"\n📋 Test 3: Get user info")
    try:
        url = "https://api.airtable.com/v0/meta/whoami"
        response = httpx.get(url, headers=headers)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print(f"   ✅ Success! User info: {response.json()}")
        else:
            print(f"   ❌ Error: {response.text[:200]}")
    except Exception as e:
        print(f"   ❌ Exception: {e}")

if __name__ == "__main__":
    simple_test() 
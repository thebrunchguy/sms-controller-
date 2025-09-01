#!/usr/bin/env python3
"""
Simple test to access the Checkins table directly
"""

import os
import httpx
from dotenv import load_dotenv

def test_table_access():
    """Test direct access to the Checkins table"""
    load_dotenv("../config/config.env")
    
    api_key = os.getenv("AIRTABLE_API_KEY")
    base_id = os.getenv("AIRTABLE_BASE_ID")
    table_name = os.getenv("AIRTABLE_PEOPLE_TABLE", "Checkins")
    
    print(f"🔍 Testing direct table access:")
    print(f"   API Key: {api_key[:20]}...")
    print(f"   Base ID: {base_id}")
    print(f"   Table: {table_name}")
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # Test 1: Try to access the table directly
    print(f"\n📋 Test 1: Direct table access")
    try:
        url = f"https://api.airtable.com/v0/{base_id}/{table_name}"
        print(f"   URL: {url}")
        
        response = httpx.get(url, headers=headers)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            records = data.get('records', [])
            print(f"   ✅ Success! Found {len(records)} records")
            
            if records:
                # Show first record structure
                first_record = records[0]
                print(f"   First record ID: {first_record.get('id')}")
                print(f"   Fields: {list(first_record.get('fields', {}).keys())}")
                
                # Show some sample data
                fields = first_record.get('fields', {})
                print(f"   Sample data:")
                for key, value in fields.items():
                    if key in ['Name', 'Email', 'Phone', 'Company', 'Role']:
                        print(f"     {key}: {value}")
        else:
            print(f"   ❌ Error: {response.text}")
            
    except Exception as e:
        print(f"   ❌ Exception: {e}")
    
    # Test 2: Try with URL encoding for table name
    print(f"\n📋 Test 2: URL encoded table name")
    try:
        import urllib.parse
        encoded_table = urllib.parse.quote(table_name)
        url = f"https://api.airtable.com/v0/{base_id}/{encoded_table}"
        print(f"   URL: {url}")
        
        response = httpx.get(url, headers=headers)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            records = data.get('records', [])
            print(f"   ✅ Success! Found {len(records)} records")
        else:
            print(f"   ❌ Error: {response.text}")
            
    except Exception as e:
        print(f"   ❌ Exception: {e}")

if __name__ == "__main__":
    test_table_access() 
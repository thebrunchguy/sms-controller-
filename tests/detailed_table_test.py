#!/usr/bin/env python3
"""
Detailed test to examine the Checkins table structure
"""

import os
import json
import httpx
from dotenv import load_dotenv

def detailed_table_test():
    """Detailed examination of the Checkins table"""
    load_dotenv("../config/config.env")
    
    api_key = os.getenv("AIRTABLE_API_KEY")
    base_id = os.getenv("AIRTABLE_BASE_ID")
    table_name = os.getenv("AIRTABLE_PEOPLE_TABLE", "Checkins")
    
    print(f"🔍 Detailed table examination:")
    print(f"   API Key: {api_key[:20]}...")
    print(f"   Base ID: {base_id}")
    print(f"   Table: {table_name}")
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    try:
        url = f"https://api.airtable.com/v0/{base_id}/{table_name}"
        print(f"\n📋 Accessing: {url}")
        
        response = httpx.get(url, headers=headers)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            records = data.get('records', [])
            print(f"   ✅ Found {len(records)} records")
            
            # Examine each record in detail
            for i, record in enumerate(records):
                print(f"\n📝 Record {i+1}:")
                print(f"   ID: {record.get('id')}")
                print(f"   Created Time: {record.get('createdTime')}")
                
                fields = record.get('fields', {})
                print(f"   Fields ({len(fields)}):")
                
                if fields:
                    for field_name, field_value in fields.items():
                        print(f"     {field_name}: {field_value}")
                else:
                    print("     (No fields found)")
                
                # Also check the raw record structure
                print(f"   Raw record keys: {list(record.keys())}")
                
        else:
            print(f"   ❌ Error: {response.text}")
            
    except Exception as e:
        print(f"   ❌ Exception: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    detailed_table_test() 
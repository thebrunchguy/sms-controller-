#!/usr/bin/env python3
"""
Explore Airtable base structure
"""

import os
import httpx
from dotenv import load_dotenv

def explore_airtable_base():
    """Explore the Airtable base to see what's available"""
    print("🔍 Exploring Airtable base structure...")
    
    # Load environment variables
    load_dotenv("../config/config.env")
    
    api_key = os.getenv("AIRTABLE_API_KEY")
    base_id = os.getenv("AIRTABLE_BASE_ID")
    
    if not api_key or not base_id:
        print("❌ Missing environment variables")
        return
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # First, let's try to get the base metadata
    base_url = f"https://api.airtable.com/v0/meta/bases/{base_id}/tables"
    
    try:
        print(f"\n📋 Getting base metadata from: {base_url}")
        response = httpx.get(base_url, headers=headers)
        
        if response.status_code == 200:
            tables = response.json()
            print(f"✅ Found {len(tables.get('tables', []))} tables:")
            
            for table in tables.get('tables', []):
                table_name = table.get('name', 'Unknown')
                table_id = table.get('id', 'Unknown')
                print(f"   📊 Table: {table_name} (ID: {table_id})")
                
                # Get fields for this table
                fields = table.get('fields', [])
                print(f"      Fields ({len(fields)}):")
                for field in fields:
                    field_name = field.get('name', 'Unknown')
                    field_type = field.get('type', 'Unknown')
                    print(f"        - {field_name} ({field_type})")
                print()
                
        else:
            print(f"❌ Error getting base metadata: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error exploring base: {e}")
    
    # Now let's try to list some actual tables by name
    print("\n🔍 Testing common table names...")
    common_table_names = [
        "People", "people", "Person", "person",
        "Check-ins", "check-ins", "Checkins", "checkins",
        "Messages", "messages", "Message", "message",
        "Contacts", "contacts", "Contact", "contact"
    ]
    
    for table_name in common_table_names:
        try:
            test_url = f"https://api.airtable.com/v0/{base_id}/{table_name}?maxRecords=1"
            response = httpx.get(test_url, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                record_count = len(data.get('records', []))
                print(f"✅ Table '{table_name}' exists with {record_count} records")
                
                # Show sample record structure
                if record_count > 0:
                    sample = data['records'][0]
                    print(f"   Sample record fields: {list(sample.get('fields', {}).keys())}")
            else:
                print(f"❌ Table '{table_name}' not found or inaccessible")
                
        except Exception as e:
            print(f"❌ Error testing table '{table_name}': {e}")

if __name__ == "__main__":
    explore_airtable_base() 
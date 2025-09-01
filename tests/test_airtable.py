#!/usr/bin/env python3
"""
Test script to verify Airtable connection
"""

import os
from dotenv import load_dotenv
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from app import airtable

def test_airtable_connection():
    """Test basic Airtable connectivity"""
    print("🔍 Testing Airtable connection...")
    
    # Load environment variables
    load_dotenv("config.env")
    
    # Check if environment variables are loaded
    api_key = os.getenv("AIRTABLE_API_KEY")
    base_id = os.getenv("AIRTABLE_BASE_ID")
    
    print(f"API Key: {api_key[:20]}..." if api_key else "❌ No API key found")
    print(f"Base ID: {base_id}")
    
    if not api_key or not base_id:
        print("❌ Missing required environment variables")
        return False
    
    try:
        # Test getting people due for check-in
        print("\n📋 Testing: get_people_due_for_checkin()")
        people = airtable.get_people_due_for_checkin()
        print(f"✅ Found {len(people)} people due for check-in")
        
        if people:
            # Show first person as example
            first_person = people[0]
            print(f"   First person: {first_person['fields'].get('Name', 'Unknown')}")
            print(f"   Phone: {first_person['fields'].get('Phone', 'No phone')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error connecting to Airtable: {e}")
        return False

if __name__ == "__main__":
    success = test_airtable_connection()
    if success:
        print("\n🎉 Airtable connection test successful!")
    else:
        print("\n💥 Airtable connection test failed!") 
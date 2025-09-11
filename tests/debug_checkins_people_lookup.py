#!/usr/bin/env python3
"""
Debug phone lookup in check-ins people table specifically
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'app'))

from airtable import _make_request, _normalize_phone
from dotenv import load_dotenv

load_dotenv()

def test_checkins_people_lookup():
    """Test phone lookup in check-ins people table"""
    phone = "+19784910236"
    normalized_phone = _normalize_phone(phone)
    print(f"Looking up normalized phone: {normalized_phone}")
    
    # Get check-ins people table
    checkins_people_table = os.getenv("AIRTABLE_CHECKINS_PEOPLE_TABLE")
    checkins_base_url = os.getenv("AIRTABLE_CHECKINS_BASE_URL")
    
    print(f"Check-ins people table: {checkins_people_table}")
    print(f"Check-ins base URL: {checkins_base_url}")
    
    if not checkins_people_table or not checkins_base_url:
        print("Missing environment variables")
        return
    
    try:
        response = _make_request("GET", checkins_people_table, base_url=checkins_base_url)
        records = response.get("records", [])
        print(f"Found {len(records)} records in check-ins people table")
        
        for record in records:
            record_phone = record.get("fields", {}).get("Phone", "")
            if record_phone:
                normalized_record_phone = _normalize_phone(record_phone)
                print(f"Record phone: '{record_phone}' -> normalized: '{normalized_record_phone}'")
                if normalized_phone == normalized_record_phone:
                    print(f"MATCH FOUND: {record}")
                    return record
        
        print("No matching phone found in check-ins people table")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_checkins_people_lookup()

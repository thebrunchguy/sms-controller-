#!/usr/bin/env python3
"""
Debug check-in creation specifically
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'app'))

from airtable import get_person_by_phone, upsert_checkin
from dotenv import load_dotenv

load_dotenv()

def test_checkin_creation():
    """Test check-in creation for David Kobrosky"""
    phone = "+19784910236"
    print(f"Looking up phone: {phone}")
    
    # Get person from check-ins people table
    person = get_person_by_phone(phone, prefer_checkins=True)
    if person:
        print(f"Found person: {person}")
        person_id = person.get('id')
        print(f"Person ID: {person_id}")
        
        # Try to create check-in
        print(f"Creating check-in for person {person_id}")
        checkin_id = upsert_checkin(person_id, "2025-01", "Sent", "Test check-in")
        if checkin_id:
            print(f"Successfully created check-in: {checkin_id}")
        else:
            print("Failed to create check-in")
    else:
        print("No person found")

if __name__ == "__main__":
    test_checkin_creation()

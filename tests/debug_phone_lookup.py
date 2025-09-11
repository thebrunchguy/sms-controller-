#!/usr/bin/env python3
"""
Debug phone lookup in check-ins people table
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'app'))

from airtable import get_person_by_phone

def test_phone_lookup():
    """Test phone lookup for David Kobrosky"""
    phone = "+19784910236"
    print(f"Looking up phone: {phone}")
    
    person = get_person_by_phone(phone)
    if person:
        print(f"Found person: {person}")
        print(f"Person ID: {person.get('id')}")
        print(f"Name: {person.get('fields', {}).get('Name')}")
        print(f"Phone: {person.get('fields', {}).get('Phone')}")
    else:
        print("No person found")

if __name__ == "__main__":
    test_phone_lookup()

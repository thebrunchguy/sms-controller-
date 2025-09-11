#!/usr/bin/env python3
"""
Debug intent handler for birthday update
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'app'))

from airtable import get_person_by_phone, get_all_people
from intent_classifier import classify_intent
from intent_handlers import IntentHandlers
from dotenv import load_dotenv

load_dotenv()

def test_intent_handler():
    """Test intent handler for birthday update"""
    phone = "+19784910236"
    body = "change david kobrosky birthday to 3/14/1999"
    
    print(f"Testing intent handler:")
    print(f"Phone: {phone}")
    print(f"Body: {body}")
    print()
    
    # Step 1: Find person in check-ins table
    print("Step 1: Finding person in check-ins table...")
    person_record = get_person_by_phone(phone, prefer_checkins=True)
    if not person_record:
        print("❌ Person not found")
        return
    print(f"✅ Found person: {person_record['fields']['Name']} (ID: {person_record['id']})")
    print()
    
    # Step 2: Classify intent
    print("Step 2: Classifying intent...")
    result = classify_intent(body, person_record['fields'])
    intent = result.get('intent', 'unknown')
    extracted_data = result.get('extracted_data', {})
    print(f"✅ Intent: {intent}")
    print(f"✅ Extracted data: {extracted_data}")
    print()
    
    # Step 3: Test intent handler
    print("Step 3: Testing intent handler...")
    success, message = IntentHandlers.handle_update_person_info(
        extracted_data, person_record['id'], person_record['fields']
    )
    print(f"✅ Success: {success}")
    print(f"✅ Message: {message}")
    print()
    
    # Step 4: Check if birthday was updated in main table
    print("Step 4: Checking main people table...")
    main_people = get_all_people()
    for person in main_people:
        fields = person.get("fields", {})
        if fields.get("Name") == "David Kobrosky":
            print(f"✅ Found David in main table: {fields.get('Birthday')}")
            break
    else:
        print("❌ David not found in main table")

if __name__ == "__main__":
    test_intent_handler()

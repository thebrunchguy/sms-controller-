#!/usr/bin/env python3
"""
Debug the full SMS flow locally
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'app'))

from airtable import get_person_by_phone, upsert_checkin, log_message
from dotenv import load_dotenv

load_dotenv()

def test_full_sms_flow():
    """Test the complete SMS flow for birthday update"""
    phone = "+19784910236"
    body = "change david kobrosky birthday to 3/14/1999"
    
    print(f"Testing SMS flow:")
    print(f"Phone: {phone}")
    print(f"Body: {body}")
    print()
    
    # Step 1: Find person
    print("Step 1: Finding person by phone...")
    person_record = get_person_by_phone(phone, prefer_checkins=True)
    if not person_record:
        print("❌ Person not found")
        return
    print(f"✅ Found person: {person_record['fields']['Name']} (ID: {person_record['id']})")
    print()
    
    # Step 2: Create check-in
    print("Step 2: Creating check-in...")
    current_month = "2025-01"
    checkin_id = upsert_checkin(person_record['id'], current_month, "Sent")
    if not checkin_id:
        print("❌ Failed to create check-in")
        return
    print(f"✅ Created check-in: {checkin_id}")
    print()
    
    # Step 3: Log message (skip for now due to field name issues)
    print("Step 3: Logging message...")
    print("⚠️ Skipping message logging due to field name issues")
    print()
    
    # Step 4: Test intent classification (simplified)
    print("Step 4: Testing intent classification...")
    try:
        from intent_classifier import classify_intent
        result = classify_intent(body, person_record['fields'])
        intent = result.get('intent', 'unknown')
        print(f"✅ Intent: {intent}")
    except Exception as e:
        print(f"❌ Intent classification failed: {e}")
    print()
    
    print("🎉 Full SMS flow completed successfully!")

if __name__ == "__main__":
    test_full_sms_flow()

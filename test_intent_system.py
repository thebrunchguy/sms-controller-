#!/usr/bin/env python3
"""
Test script for the intent-based routing system
"""

import os
import sys
sys.path.append('app')

from intent_classifier import classify_intent

def test_intent_classification():
    """Test the intent classification with sample messages"""
    
    # Sample person context
    person_context = {
        "Name": "David Kobrosky",
        "Company": "Tech Corp",
        "Role": "Software Engineer",
        "City": "San Francisco",
        "Tags": ["developer", "python"]
    }
    
    # Test messages
    test_messages = [
        "hey, can you update david kobrosky's birthday to be 03/14/1999?",
        "Hey can you tag David with tag 'mentor'",
        "can you remind me to reach out to this person in a few months?",
        "note: david mentioned he's interested in the PM role",
        "schedule a follow-up next month to discuss the project",
        "no change",
        "yes",
        "stop"
    ]
    
    print("🧪 Testing Intent Classification System")
    print("=" * 50)
    
    for message in test_messages:
        print(f"\n�� Message: '{message}'")
        
        try:
            result = classify_intent(message, person_context)
            print(f"   Intent: {result.get('intent', 'unknown')}")
            print(f"   Confidence: {result.get('confidence', 0):.2f}")
            print(f"   Target Table: {result.get('target_table', 'None')}")
            print(f"   Extracted Data: {result.get('extracted_data', {})}")
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    print("\n" + "=" * 50)
    print("✅ Intent classification test completed")

if __name__ == "__main__":
    test_intent_classification() 
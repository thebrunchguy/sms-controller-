#!/usr/bin/env python3
"""
Test SMS functionality by sending a message to David
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app import twilio_utils
from dotenv import load_dotenv

def test_sms_to_david():
    """Test sending SMS to David"""
    print("📱 Testing SMS functionality...")
    
    # Load environment variables
    config_path = os.path.join(os.path.dirname(__file__), "..", "config", "config.env")
    load_dotenv(config_path)
    
    # David's phone number from Airtable
    david_phone = "+19784910236"
    
    # Test message
    test_message = "🧪 Test message from Monthly SMS Check-in app! This is a test of the SMS functionality. Reply STOP to opt out."
    
    print(f"📤 Sending test SMS to: {david_phone}")
    print(f"📝 Message: {test_message}")
    
    try:
        # Send the SMS
        message_sid = twilio_utils.send_sms(
            to=david_phone,
            body=test_message,
            status_callback_url=None  # No callback for this test
        )
        
        if message_sid:
            print(f"✅ SMS sent successfully!")
            print(f"   Message SID: {message_sid}")
            print(f"   📱 Check David's phone for the message")
            
            # Get message status
            print(f"\n📊 Getting message status...")
            status = twilio_utils.get_message_status(message_sid)
            if status:
                print(f"   Status: {status.get('status', 'Unknown')}")
                print(f"   Direction: {status.get('direction', 'Unknown')}")
                print(f"   From: {status.get('from', 'Unknown')}")
                print(f"   To: {status.get('to', 'Unknown')}")
            else:
                print(f"   ❌ Could not get message status")
                
        else:
            print(f"❌ Failed to send SMS")
            
    except Exception as e:
        print(f"❌ Error sending SMS: {e}")
        import traceback
        traceback.print_exc()

def test_phone_formatting():
    """Test phone number formatting"""
    print(f"\n🔢 Testing phone number formatting...")
    
    test_numbers = [
        "9784910236",
        "(978) 491-0236", 
        "+1 (978) 491-0236",
        "978-491-0236"
    ]
    
    for number in test_numbers:
        formatted = twilio_utils.format_phone_number(number)
        print(f"   {number} → {formatted}")

if __name__ == "__main__":
    print("🚀 SMS Test Suite")
    print("=" * 50)
    
    # Test phone formatting first
    test_phone_formatting()
    
    # Test actual SMS sending
    test_sms_to_david()
    
    print("\n" + "=" * 50)
    print("📱 SMS test completed!") 
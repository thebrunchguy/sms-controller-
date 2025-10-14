#!/usr/bin/env python3
"""
Test different phone number formats
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app import twilio_utils
from dotenv import load_dotenv

def test_phone_formats():
    """Test different phone number formats"""
    print("🔢 Testing different phone number formats...")
    
    # Load environment variables
    config_path = os.path.join(os.path.dirname(__file__), "..", "config", "config.env")
    load_dotenv(config_path)
    
    # Test different formats of David's number
    test_numbers = [
        "+19784910236",      # E.164 format
        "19784910236",       # Without +
        "9784910236",        # 10 digits
        "1-978-491-0236",    # With dashes
        "(978) 491-0236"     # With parentheses
    ]
    
    for phone in test_numbers:
        print(f"\n📱 Testing format: {phone}")
        
        # Format the number
        formatted = twilio_utils.format_phone_number(phone)
        print(f"   Formatted: {formatted}")
        
        # Try to send a very short test message
        test_message = f"Test {phone[-4:]}"  # Last 4 digits for identification
        
        try:
            message_sid = twilio_utils.send_sms(
                to=formatted,
                body=test_message,
                status_callback_url=None
            )
            
            if message_sid:
                print(f"   ✅ SMS sent: {message_sid}")
                
                # Check status immediately
                status = twilio_utils.get_message_status(message_sid)
                if status:
                    print(f"   Status: {status.get('status')}")
                    if status.get('status') == 'delivered':
                        print(f"   🎉 SUCCESS! This format works!")
                        return formatted  # Return the working format
            else:
                print(f"   ❌ SMS failed to send")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    return None

def test_twilio_number():
    """Test if we can send to our own Twilio number"""
    print(f"\n📱 Testing if we can send to our own Twilio number...")
    
    twilio_number = os.getenv("TWILIO_PHONE_NUMBER")
    if twilio_number:
        print(f"   Twilio number: {twilio_number}")
        
        try:
            message_sid = twilio_utils.send_sms(
                to=twilio_number,
                body="Test to our own Twilio number",
                status_callback_url=None
            )
            
            if message_sid:
                print(f"   ✅ SMS sent to our number: {message_sid}")
                status = twilio_utils.get_message_status(message_sid)
                if status:
                    print(f"   Status: {status.get('status')}")
            else:
                print(f"   ❌ Failed to send to our number")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
    else:
        print(f"   ❌ No Twilio number configured")

if __name__ == "__main__":
    working_format = test_phone_formats()
    test_twilio_number()
    
    if working_format:
        print(f"\n🎉 Found working phone format: {working_format}")
    else:
        print(f"\n❌ No working phone format found")
        print(f"   This suggests a deeper issue with Twilio configuration") 
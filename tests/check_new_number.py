#!/usr/bin/env python3
"""
Check the new Twilio number status
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app import twilio_utils
from dotenv import load_dotenv

def check_new_twilio_number():
    """Check the new Twilio number configuration"""
    print("🔍 Checking new Twilio number configuration...")
    
    # Load environment variables
    config_path = os.path.join(os.path.dirname(__file__), "..", "config", "config.env")
    load_dotenv(config_path)
    
    # Check environment variables
    print(f"📋 Environment variables:")
    print(f"   TWILIO_ACCOUNT_SID: {os.getenv('TWILIO_ACCOUNT_SID', 'NOT SET')[:20]}...")
    print(f"   TWILIO_AUTH_TOKEN: {os.getenv('TWILIO_AUTH_TOKEN', 'NOT SET')[:20]}...")
    print(f"   TWILIO_PHONE_NUMBER: {os.getenv('TWILIO_PHONE_NUMBER', 'NOT SET')}")
    
    # Check the specific message that failed
    message_sid = "SMccbf40ec3dd35f0209305f4720ccb5c3"
    print(f"\n📱 Checking failed message: {message_sid}")
    
    try:
        status = twilio_utils.get_message_status(message_sid)
        if status:
            print(f"   Status: {status.get('status')}")
            print(f"   Error Code: {status.get('error_code', 'None')}")
            print(f"   Error Message: {status.get('error_message', 'None')}")
            print(f"   From: {status.get('from', 'None')}")
            print(f"   To: {status.get('to', 'None')}")
            print(f"   Body: {status.get('body', 'None')}")
            
            # Look up error code meaning
            error_code = status.get('error_code')
            if error_code == '30034':
                print(f"\n🔍 Error 30034 typically means:")
                print(f"   - Invalid phone number")
                print(f"   - Number not properly configured")
                print(f"   - Account restrictions")
        else:
            print(f"   ❌ Could not get message status")
            
    except Exception as e:
        print(f"   ❌ Error checking message: {e}")
    
    # Try to send a very simple test message
    print(f"\n🧪 Testing with very simple message...")
    try:
        simple_sid = twilio_utils.send_sms(
            to="9784910236",
            body="Test new number",
            status_callback_url=None
        )
        
        if simple_sid:
            print(f"   ✅ Simple message sent: {simple_sid}")
            
            # Check its status
            import time
            time.sleep(3)
            simple_status = twilio_utils.get_message_status(simple_sid)
            if simple_status:
                print(f"   Status: {simple_status.get('status')}")
                print(f"   Error: {simple_status.get('error_code', 'None')}")
        else:
            print(f"   ❌ Simple message failed to send")
            
    except Exception as e:
        print(f"   ❌ Error sending simple message: {e}")

if __name__ == "__main__":
    check_new_twilio_number() 
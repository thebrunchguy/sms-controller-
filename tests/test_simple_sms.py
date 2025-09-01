#!/usr/bin/env python3
"""
Test simple SMS without special characters
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app import twilio_utils
from dotenv import load_dotenv

def test_simple_sms():
    """Test sending a very simple SMS"""
    print("📱 Testing simple SMS...")
    
    # Load environment variables
    config_path = os.path.join(os.path.dirname(__file__), "..", "config", "config.env")
    load_dotenv(config_path)
    
    # David's phone number
    david_phone = "+19784910236"
    
    # Very simple test message - no emojis, no special characters
    simple_message = "Test message from Monthly SMS Check-in app. This is a simple test without special characters."
    
    print(f"📤 Sending simple SMS to: {david_phone}")
    print(f"📝 Message: {simple_message}")
    
    try:
        # Send the SMS
        message_sid = twilio_utils.send_sms(
            to=david_phone,
            body=simple_message,
            status_callback_url=None
        )
        
        if message_sid:
            print(f"✅ Simple SMS sent successfully!")
            print(f"   Message SID: {message_sid}")
            
            # Wait a moment and check status
            import time
            print(f"   Waiting 5 seconds to check status...")
            time.sleep(5)
            
            status = twilio_utils.get_message_status(message_sid)
            if status:
                print(f"   Status: {status.get('status')}")
                print(f"   Error Code: {status.get('error_code', 'None')}")
                print(f"   Error Message: {status.get('error_message', 'None')}")
                
                if status.get('status') == 'delivered':
                    print(f"   🎉 Message delivered to your phone!")
                elif status.get('status') == 'sent':
                    print(f"   📤 Message sent to carrier, should arrive shortly")
                elif status.get('status') == 'undelivered':
                    print(f"   ❌ Message undelivered - there's a delivery issue")
                else:
                    print(f"   ❓ Unknown status: {status.get('status')}")
            else:
                print(f"   ❌ Could not get message status")
                
        else:
            print(f"❌ Failed to send simple SMS")
            
    except Exception as e:
        print(f"❌ Error sending simple SMS: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_simple_sms() 
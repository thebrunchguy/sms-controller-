#!/usr/bin/env python3
"""
Send a single test SMS to 9784910236
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app import twilio_utils
from dotenv import load_dotenv

def send_single_test():
    """Send a single test SMS"""
    print("📱 Sending single test SMS...")
    
    # Load environment variables
    config_path = os.path.join(os.path.dirname(__file__), "..", "config", "config.env")
    load_dotenv(config_path)
    
    # Your cell number
    your_phone = "9784910236"
    
    # Simple test message
    test_message = "Test message from Monthly SMS Check-in app. Please let me know if you receive this."
    
    print(f"📤 Sending test SMS to: {your_phone}")
    print(f"📝 Message: {test_message}")
    
    try:
        # Send the SMS
        message_sid = twilio_utils.send_sms(
            to=your_phone,
            body=test_message,
            status_callback_url=None
        )
        
        if message_sid:
            print(f"✅ SMS sent successfully!")
            print(f"   Message SID: {message_sid}")
            print(f"   📱 Check your phone for the message")
            
            # Check status
            print(f"\n📊 Checking message status...")
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
                    print(f"   📋 Status: {status.get('status')}")
            else:
                print(f"   ❌ Could not get message status")
                
        else:
            print(f"❌ Failed to send SMS")
            
    except Exception as e:
        print(f"❌ Error sending SMS: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    send_single_test() 
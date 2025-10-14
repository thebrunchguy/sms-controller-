#!/usr/bin/env python3
"""
Test sending the specific birthday update SMS message
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app import twilio_utils
from dotenv import load_dotenv

def test_birthday_update_sms():
    """Test sending the birthday update SMS message"""
    print("📱 Testing Birthday Update SMS...")
    
    # Load environment variables
    config_path = os.path.join(os.path.dirname(__file__), "..", "config", "config.env")
    load_dotenv(config_path)
    
    # Your phone number
    your_phone = "9784910236"
    
    # The specific message you want to test
    birthday_message = "change david kobrosky's birthday to 3/14/1999"
    
    print(f"📤 Sending birthday update SMS to: {your_phone}")
    print(f"📝 Message: '{birthday_message}'")
    
    try:
        # Send the SMS
        message_sid = twilio_utils.send_sms(
            to=your_phone,
            body=birthday_message,
            status_callback_url=None
        )
        
        if message_sid:
            print(f"✅ Birthday update SMS sent successfully!")
            print(f"   Message SID: {message_sid}")
            print(f"   📱 Check your phone for the message")
            print(f"   🔄 Now reply to that message to test the processing")
            
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
            print(f"❌ Failed to send birthday update SMS")
            
    except Exception as e:
        print(f"❌ Error sending birthday update SMS: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🎂 Birthday Update SMS Test")
    print("=" * 50)
    test_birthday_update_sms()
    print("\n" + "=" * 50)
    print("📱 Birthday update SMS test completed!")
    print("💡 After you receive the message, reply to it to test the processing")

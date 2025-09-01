#!/usr/bin/env python3
"""
Check Twilio message status in detail
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app import twilio_utils
from dotenv import load_dotenv

def check_message_status():
    """Check the status of the last sent message"""
    print("🔍 Checking Twilio message status...")
    
    # Load environment variables
    config_path = os.path.join(os.path.dirname(__file__), "..", "config", "config.env")
    load_dotenv(config_path)
    
    # The message SID from our test
    message_sid = "SM890890d095bfce314d212b302612ea62"
    
    print(f"📱 Checking message: {message_sid}")
    
    try:
        # Get detailed message status
        status = twilio_utils.get_message_status(message_sid)
        
        if status:
            print(f"✅ Message found in Twilio:")
            print(f"   SID: {status.get('sid')}")
            print(f"   Status: {status.get('status')}")
            print(f"   Direction: {status.get('direction')}")
            print(f"   From: {status.get('from')}")
            print(f"   To: {status.get('to')}")
            print(f"   Body: {status.get('body')}")
            print(f"   Date Sent: {status.get('date_sent')}")
            print(f"   Error Code: {status.get('error_code', 'None')}")
            print(f"   Error Message: {status.get('error_message', 'None')}")
            
            # Check what the status means
            message_status = status.get('status', '').lower()
            if message_status == 'sent':
                print(f"\n📤 Status 'sent' means Twilio sent the message to the carrier")
                print(f"   The message should be delivered to your phone shortly")
            elif message_status == 'delivered':
                print(f"\n✅ Status 'delivered' means the message reached your phone")
            elif message_status == 'failed':
                print(f"\n❌ Status 'failed' means there was an error")
                print(f"   Error: {status.get('error_message', 'Unknown error')}")
            elif message_status == 'undelivered':
                print(f"\n❌ Status 'undelivered' means the carrier couldn't deliver it")
            else:
                print(f"\n❓ Unknown status: {message_status}")
                
        else:
            print(f"❌ Could not get message status")
            
    except Exception as e:
        print(f"❌ Error checking message status: {e}")
        import traceback
        traceback.print_exc()

def check_twilio_account():
    """Check Twilio account status"""
    print(f"\n🔍 Checking Twilio account status...")
    
    try:
        # Try to send a very simple test message
        test_sid = twilio_utils.send_sms(
            to="+19784910236",
            body="Test 2 - Simple message",
            status_callback_url=None
        )
        
        if test_sid:
            print(f"✅ Test message 2 sent successfully: {test_sid}")
            
            # Check its status immediately
            status = twilio_utils.get_message_status(test_sid)
            if status:
                print(f"   Status: {status.get('status')}")
                print(f"   Error: {status.get('error_message', 'None')}")
        else:
            print(f"❌ Test message 2 failed to send")
            
    except Exception as e:
        print(f"❌ Error sending test message 2: {e}")

if __name__ == "__main__":
    check_message_status()
    check_twilio_account() 
#!/usr/bin/env python3
"""
Check final status of all test messages
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app import twilio_utils
from dotenv import load_dotenv

def check_message_statuses():
    """Check status of all test messages"""
    print("🔍 Checking final status of all test messages...")
    
    # Load environment variables
    config_path = os.path.join(os.path.dirname(__file__), "..", "config", "config.env")
    load_dotenv(config_path)
    
    # All the message SIDs from our tests
    message_sids = [
        "SM890890d095bfce314d212b302612ea62",  # First test
        "SMccacfd0a6de1e58b8c07267408ae8cb8",  # Second test
        "SM868824aa91390a1e749d81d8b27d4ff9",  # Simple test
        "SMcaa45f4d0d122735421bcb55684a542b",  # Format test 1
        "SM714b4f3625b763cc12080c560d04410c",  # Format test 2
        "SM6912b7d4b857912c8e72e9f7d6e75d32",  # Format test 3
        "SM21847c441f4555cbcc2f8c99f49f82f2",  # Format test 4
        "SM463606ab9bcad30200b8b36895645655"   # Format test 5
    ]
    
    delivered_count = 0
    total_count = len(message_sids)
    
    for i, sid in enumerate(message_sids, 1):
        print(f"\n📱 Message {i}/{total_count}: {sid}")
        
        try:
            status = twilio_utils.get_message_status(sid)
            
            if status:
                message_status = status.get('status', 'Unknown')
                error_code = status.get('error_code', 'None')
                error_message = status.get('error_message', 'None')
                
                print(f"   Status: {message_status}")
                print(f"   Error Code: {error_code}")
                print(f"   Error Message: {error_message}")
                
                if message_status == 'delivered':
                    delivered_count += 1
                    print(f"   🎉 DELIVERED!")
                elif message_status == 'sent':
                    print(f"   📤 Sent to carrier")
                elif message_status == 'sending':
                    print(f"   📤 Still sending...")
                elif message_status == 'queued':
                    print(f"   📋 In queue")
                elif message_status == 'undelivered':
                    print(f"   ❌ Undelivered")
                else:
                    print(f"   ❓ Unknown status: {message_status}")
            else:
                print(f"   ❌ Could not get status")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    print(f"\n📊 Summary:")
    print(f"   Total messages: {total_count}")
    print(f"   Delivered: {delivered_count}")
    print(f"   Success rate: {(delivered_count/total_count)*100:.1f}%")
    
    if delivered_count > 0:
        print(f"   🎉 At least one message was delivered!")
    else:
        print(f"   ❌ No messages were delivered")
        print(f"   This suggests a carrier or phone configuration issue")

if __name__ == "__main__":
    check_message_statuses() 
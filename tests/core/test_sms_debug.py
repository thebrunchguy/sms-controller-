#!/usr/bin/env python3
"""
Debug SMS test to check environment variables
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app import twilio_utils
from dotenv import load_dotenv

def debug_sms_test():
    """Debug SMS functionality step by step"""
    print("🔍 Debugging SMS functionality...")
    
    # Check environment before loading
    print(f"\n📋 Environment before loading config:")
    print(f"   TWILIO_ACCOUNT_SID: {os.getenv('TWILIO_ACCOUNT_SID', 'NOT SET')}")
    print(f"   TWILIO_AUTH_TOKEN: {os.getenv('TWILIO_AUTH_TOKEN', 'NOT SET')[:20] if os.getenv('TWILIO_AUTH_TOKEN') else 'NOT SET'}...")
    print(f"   TWILIO_PHONE_NUMBER: {os.getenv('TWILIO_PHONE_NUMBER', 'NOT SET')}")
    
    # Load environment variables
    config_path = os.path.join(os.path.dirname(__file__), "..", "config", "config.env")
    print(f"\n📋 Loading config from: {config_path}")
    load_dotenv(config_path)
    
    # Check environment after loading
    print(f"\n📋 Environment after loading config:")
    print(f"   TWILIO_ACCOUNT_SID: {os.getenv('TWILIO_ACCOUNT_SID', 'NOT SET')}")
    print(f"   TWILIO_AUTH_TOKEN: {os.getenv('TWILIO_AUTH_TOKEN', 'NOT SET')[:20] if os.getenv('TWILIO_AUTH_TOKEN') else 'NOT SET'}...")
    print(f"   TWILIO_PHONE_NUMBER: {os.getenv('TWILIO_PHONE_NUMBER', 'NOT SET')}")
    
    # Check if the module can see the environment variables
    print(f"\n📋 Checking module environment access:")
    print(f"   From module TWILIO_ACCOUNT_SID: {twilio_utils.TWILIO_ACCOUNT_SID}")
    print(f"   From module TWILIO_AUTH_TOKEN: {twilio_utils.TWILIO_AUTH_TOKEN[:20] if twilio_utils.TWILIO_AUTH_TOKEN else 'NOT SET'}...")
    print(f"   From module TWILIO_PHONE_NUMBER: {twilio_utils.TWILIO_PHONE_NUMBER}")
    
    # Try to get the client
    print(f"\n📋 Testing client initialization:")
    try:
        client = twilio_utils._get_twilio_client()
        if client:
            print(f"   ✅ Twilio client initialized successfully")
        else:
            print(f"   ❌ Twilio client initialization failed")
    except Exception as e:
        print(f"   ❌ Error initializing client: {e}")

if __name__ == "__main__":
    debug_sms_test() 
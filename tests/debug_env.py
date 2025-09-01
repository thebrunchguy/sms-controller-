#!/usr/bin/env python3
"""
Debug environment variable loading
"""

import os
from dotenv import load_dotenv

def debug_environment():
    """Debug environment variable loading"""
    print("🔍 Debugging environment variables...")
    
    # Check current environment
    print(f"\n📋 Current environment variables:")
    print(f"   TWILIO_ACCOUNT_SID: {os.getenv('TWILIO_ACCOUNT_SID', 'NOT SET')}")
    print(f"   TWILIO_AUTH_TOKEN: {os.getenv('TWILIO_AUTH_TOKEN', 'NOT SET')[:20] if os.getenv('TWILIO_AUTH_TOKEN') else 'NOT SET'}...")
    print(f"   TWILIO_PHONE_NUMBER: {os.getenv('TWILIO_PHONE_NUMBER', 'NOT SET')}")
    
    # Try to load from config
    print(f"\n📋 Loading from config/config.env...")
    config_path = os.path.join(os.path.dirname(__file__), "..", "config", "config.env")
    load_dotenv(config_path)
    
    print(f"\n📋 After loading config:")
    print(f"   TWILIO_ACCOUNT_SID: {os.getenv('TWILIO_ACCOUNT_SID', 'NOT SET')}")
    print(f"   TWILIO_AUTH_TOKEN: {os.getenv('TWILIO_AUTH_TOKEN', 'NOT SET')[:20] if os.getenv('TWILIO_AUTH_TOKEN') else 'NOT SET'}...")
    print(f"   TWILIO_PHONE_NUMBER: {os.getenv('TWILIO_PHONE_NUMBER', 'NOT SET')}")
    
    # Check if file exists
    config_path = os.path.join(os.path.dirname(__file__), "..", "config", "config.env")
    print(f"\n📋 Config file check:")
    print(f"   Path: {config_path}")
    print(f"   Exists: {os.path.exists(config_path)}")
    print(f"   Absolute path: {os.path.abspath(config_path)}")
    
    # Try to read the file directly
    try:
        with open(config_path, 'r') as f:
            content = f.read()
            print(f"\n📋 Config file content (first 200 chars):")
            print(f"   {content[:200]}...")
    except Exception as e:
        print(f"   ❌ Error reading file: {e}")

if __name__ == "__main__":
    debug_environment() 
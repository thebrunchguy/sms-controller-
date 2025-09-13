#!/usr/bin/env python3
"""
Test script to fix phone number formatting
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '.'))

from app import admin_sms

def test_phone_command():
    """Test the add phone command to fix the formatting"""
    print("🧪 Testing Phone Number Fix")
    print("=" * 50)
    
    # Test the add phone command parsing
    command = "add phone andrew awad (832) 474-3817"
    parsed = admin_sms.parse_admin_command(command)
    
    if parsed:
        print(f"✅ Command parsed: {parsed}")
        print(f"   Name: '{parsed['name']}'")
        print(f"   Phone: '{parsed['phone']}'")
        
        # This would update the phone field to just the clean number
        print(f"\n📱 This would update the phone field to: '{parsed['phone']}'")
        print("   (removing the 'awad' text)")
    else:
        print(f"❌ Command failed to parse: '{command}'")

if __name__ == "__main__":
    test_phone_command()

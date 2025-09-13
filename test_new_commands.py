#!/usr/bin/env python3
"""
Test script for the new admin commands
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '.'))

from app import admin_sms

def test_new_commands():
    """Test the new admin commands parsing"""
    print("🧪 Testing New Admin Commands")
    print("=" * 50)
    
    # Test commands
    test_commands = [
        "add email John Doe john@example.com",
        "add phone Jane Smith +1234567890", 
        "add linkedin Bob Johnson https://linkedin.com/in/bob",
        "ADD EMAIL Sarah Wilson sarah@test.com",
        "invalid command"
    ]
    
    for cmd in test_commands:
        parsed = admin_sms.parse_admin_command(cmd)
        if parsed:
            print(f"✅ '{cmd}' → Parsed: {parsed}")
        else:
            print(f"❌ '{cmd}' → Not parsed")
    
    print("\n📋 Updated Help Text")
    print("=" * 30)
    help_text = admin_sms.get_admin_help()
    print(help_text)
    
    print("\n🎯 New commands are ready!")
    print("📱 Test them by texting the commands to your Twilio number")

if __name__ == "__main__":
    test_new_commands()

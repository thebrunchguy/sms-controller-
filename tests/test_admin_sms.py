#!/usr/bin/env python3
"""
Test admin SMS functionality
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app import admin_sms
from dotenv import load_dotenv

def test_admin_commands():
    """Test admin command parsing and execution"""
    print("🔐 Testing Admin SMS Commands")
    print("=" * 50)
    
    # Load environment variables
    config_path = os.path.join(os.path.dirname(__file__), "..", "config", "config.env")
    load_dotenv(config_path)
    
    # Test admin number detection
    print(f"\n📱 Testing admin number detection:")
    test_numbers = ["+19784910236", "9784910236", "+15551234567", "5551234567"]
    
    for number in test_numbers:
        is_admin = admin_sms.is_admin_number(number)
        print(f"   {number}: {'✅ Admin' if is_admin else '❌ Not Admin'}")
    
    # Test command parsing
    print(f"\n📝 Testing command parsing:")
    test_commands = [
        "add birthday John Doe 1990-05-15",
        "change role John Doe Senior Developer",
        "change company John Doe Google",
        "invalid command",
        "add birthday John Doe invalid-date",
        "change role John Doe",
        "change company"
    ]
    
    for command in test_commands:
        parsed = admin_sms.parse_admin_command(command)
        if parsed:
            print(f"   ✅ '{command}' → {parsed}")
        else:
            print(f"   ❌ '{command}' → Not recognized")
    
    # Test help message
    print(f"\n📋 Testing help message:")
    help_text = admin_sms.get_admin_help()
    print(f"   Help text length: {len(help_text)} characters")
    print(f"   Preview: {help_text[:100]}...")
    
    # Test person finding (this will require Airtable data)
    print(f"\n🔍 Testing person finding:")
    try:
        # This will only work if you have people in your Airtable
        people = admin_sms.find_person_by_name("David Kobrosky")
        if people:
            print(f"   ✅ Found David Kobrosky in Airtable")
        else:
            print(f"   ❌ David Kobrosky not found in Airtable")
    except Exception as e:
        print(f"   ❌ Error testing person finding: {e}")

def test_specific_command(command_text: str):
    """Test a specific admin command"""
    print(f"\n🧪 Testing specific command: '{command_text}'")
    
    # Parse the command
    parsed = admin_sms.parse_admin_command(command_text)
    if parsed:
        print(f"   ✅ Parsed: {parsed}")
        
        # Try to execute it
        try:
            success, message = admin_sms.execute_admin_command(parsed)
            print(f"   Execution: {'✅ Success' if success else '❌ Failed'}")
            print(f"   Message: {message}")
        except Exception as e:
            print(f"   ❌ Execution error: {e}")
    else:
        print(f"   ❌ Command not recognized")

if __name__ == "__main__":
    test_admin_commands()
    
    # Test specific commands if provided
    if len(sys.argv) > 1:
        command = " ".join(sys.argv[1:])
        test_specific_command(command)
    else:
        print(f"\n💡 To test a specific command, run:")
        print(f"   python3 tests/test_admin_sms.py 'add birthday John Doe 1990-05-15'") 
#!/usr/bin/env python3
"""
Test script for improved regex patterns
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '.'))

from app import admin_sms

def test_improved_patterns():
    """Test the improved regex patterns"""
    print("🧪 Testing Improved Regex Patterns")
    print("=" * 50)
    
    test_commands = [
        "add phone andrew awad (832) 474-3817",
        "add email john doe john@example.com", 
        "add linkedin jane smith https://linkedin.com/in/janesmith",
        "add phone sarah wilson 555-123-4567",
        "add email mike johnson mike.johnson@company.co.uk",
        "add linkedin bob brown linkedin.com/in/bobbrown"
    ]
    
    for cmd in test_commands:
        parsed = admin_sms.parse_admin_command(cmd)
        if parsed:
            print(f"✅ '{cmd}'")
            print(f"   → Name: '{parsed['name']}'")
            print(f"   → Value: '{parsed[list(parsed.keys())[-1]]}'")
        else:
            print(f"❌ '{cmd}' → Not parsed")
        print()

if __name__ == "__main__":
    test_improved_patterns()

#!/usr/bin/env python3
"""
Test Notes table write access
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from airtable import _make_request

def test_notes_write():
    print('=== TESTING NOTES TABLE WRITE ===')

    # Test writing to Notes table
    try:
        data = {
            'records': [{
                'fields': {
                    'Note': 'Test note from API',
                    'Date': '2025-10-24'
                }
            }]
        }
        
        response = _make_request('POST', 'tblHuiucbEO4aWWlv', data, base_url='https://api.airtable.com/v0/appLAkkrfDl7fxeQz')
        if response:
            print('✅ Successfully wrote to Notes table')
            print(f'Response: {response}')
        else:
            print('❌ Failed to write to Notes table')
    except Exception as e:
        print(f'❌ Error: {e}')

if __name__ == "__main__":
    test_notes_write()

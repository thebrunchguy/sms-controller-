#!/usr/bin/env python3
"""
Test Notes table access
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from airtable import _make_request

def test_notes_access():
    print('=== TESTING NOTES TABLE ACCESS ===')

    # Test reading from Notes table
    try:
        response = _make_request('GET', 'tblHuiucbEO4aWWlv', base_url='https://api.airtable.com/v0/appLAkkrfDl7fxeQz')
        if response:
            print('✅ Successfully connected to Notes table')
            print(f'Found {len(response.get("records", []))} records')
            
            # Show first few records
            records = response.get('records', [])
            for i, record in enumerate(records[:3], 1):
                print(f'\n--- Record {i} ---')
                fields = record.get('fields', {})
                print(f'ID: {record.get("id")}')
                print(f'Fields: {list(fields.keys())}')
        else:
            print('❌ Failed to connect to Notes table')
    except Exception as e:
        print(f'❌ Error: {e}')

if __name__ == "__main__":
    test_notes_access()

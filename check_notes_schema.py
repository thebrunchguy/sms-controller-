#!/usr/bin/env python3
"""
Check Notes table schema
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from airtable import _make_request

def check_notes_schema():
    print('=== CHECKING NOTES TABLE SCHEMA ===')

    try:
        # Get table schema
        response = _make_request('GET', 'tblHuiucbEO4aWWlv', base_url='https://api.airtable.com/v0/appLAkkrfDl7fxeQz', params={'maxRecords': 1})
        if response:
            print('✅ Successfully connected to Notes table')
            records = response.get('records', [])
            if records:
                fields = records[0].get('fields', {})
                print(f'Available fields: {list(fields.keys())}')
            else:
                print('No records found, checking base schema...')
                # Try to get base schema
                base_response = _make_request('GET', '', base_url='https://api.airtable.com/v0/meta/bases/appLAkkrfDl7fxeQz/tables')
                if base_response:
                    print(f'Base schema response: {base_response}')
        else:
            print('❌ Failed to connect to Notes table')
    except Exception as e:
        print(f'❌ Error: {e}')

if __name__ == "__main__":
    check_notes_schema()

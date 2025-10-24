#!/usr/bin/env python3
"""
Test note creation functionality
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from airtable import find_person_in_notes_base, create_note

def test_note_creation():
    print('=== TESTING NOTE CREATION ===')

    # Test finding Devesh in notes base
    print('1. Looking for Devesh in notes base...')
    person = find_person_in_notes_base('devesh')
    if person:
        print(f'✅ Found: {person.get("fields", {}).get("Name", "Unknown")} (ID: {person.get("id", "Unknown")})')
        
        # Test creating a note
        print('\n2. Testing note creation...')
        note_data = {
            'Note': 'Test note: we got dinner yesterday',
            'Link to Notes Main View': [person['id']],
            'Type of note': ['Interaction'],
            'Date': '2025-10-24'
        }
        
        success = create_note(note_data)
        if success:
            print('✅ Note created successfully!')
        else:
            print('❌ Note creation failed')
    else:
        print('❌ Could not find Devesh in notes base')

if __name__ == "__main__":
    test_note_creation()

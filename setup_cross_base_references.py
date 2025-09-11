#!/usr/bin/env python3
"""
Script to set up cross-base references for SMS check-ins
This creates a People table in the check-ins base and copies people from the main base
"""

import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('config/config.env')

# Configuration
MAIN_BASE_ID = os.getenv('AIRTABLE_BASE_ID')
MAIN_PEOPLE_TABLE = os.getenv('AIRTABLE_PEOPLE_TABLE')
CHECKINS_BASE_ID = os.getenv('AIRTABLE_CHECKINS_BASE_ID')
API_KEY = os.getenv('AIRTABLE_API_KEY')

def get_headers():
    return {
        'Authorization': f'Bearer {API_KEY}',
        'Content-Type': 'application/json'
    }

def create_people_table_in_checkins_base():
    """Create a People table in the check-ins base"""
    print("Creating People table in check-ins base...")
    
    # First, check if a People table already exists
    url = f'https://api.airtable.com/v0/meta/bases/{CHECKINS_BASE_ID}/tables'
    response = requests.get(url, headers=get_headers())
    
    if response.status_code == 200:
        tables = response.json().get('tables', [])
        for table in tables:
            if table.get('name', '').lower() in ['people', 'person']:
                print(f"People table already exists: {table.get('name')} (ID: {table.get('id')})")
                return table.get('id')
    
    # Create the People table
    url = f'https://api.airtable.com/v0/meta/bases/{CHECKINS_BASE_ID}/tables'
    table_data = {
        "name": "People",
        "fields": [
            {
                "name": "Name",
                "type": "singleLineText"
            },
            {
                "name": "Phone",
                "type": "phoneNumber"
            },
            {
                "name": "Email",
                "type": "email"
            },
            {
                "name": "Birthday",
                "type": "date"
            },
            {
                "name": "Original ID",
                "type": "singleLineText",
                "description": "ID from the main people base"
            }
        ]
    }
    
    response = requests.post(url, headers=get_headers(), json=table_data)
    if response.status_code == 200:
        table_id = response.json().get('id')
        print(f"✅ Created People table with ID: {table_id}")
        return table_id
    else:
        print(f"❌ Failed to create People table: {response.text}")
        return None

def copy_people_to_checkins_base(people_table_id):
    """Copy people from main base to check-ins base"""
    print("Copying people from main base to check-ins base...")
    
    # Get people from main base
    url = f'https://api.airtable.com/v0/{MAIN_BASE_ID}/{MAIN_PEOPLE_TABLE}'
    response = requests.get(url, headers=get_headers())
    
    if response.status_code != 200:
        print(f"❌ Failed to get people from main base: {response.text}")
        return
    
    people = response.json().get('records', [])
    print(f"Found {len(people)} people in main base")
    
    # Prepare records for check-ins base
    records_to_create = []
    for person in people:
        fields = person.get('fields', {})
        record = {
            "fields": {
                "Name": fields.get('Name', ''),
                "Phone": fields.get('Phone', ''),
                "Email": fields.get('Email', ''),
                "Birthday": fields.get('Birthday', ''),
                "Original ID": person.get('id', '')
            }
        }
        records_to_create.append(record)
    
    # Create records in check-ins base
    url = f'https://api.airtable.com/v0/{CHECKINS_BASE_ID}/{people_table_id}'
    
    # Airtable allows up to 10 records per request
    batch_size = 10
    for i in range(0, len(records_to_create), batch_size):
        batch = records_to_create[i:i + batch_size]
        data = {"records": batch}
        
        response = requests.post(url, headers=get_headers(), json=data)
        if response.status_code == 200:
            created_count = len(response.json().get('records', []))
            print(f"✅ Created {created_count} people records (batch {i//batch_size + 1})")
        else:
            print(f"❌ Failed to create batch: {response.text}")

def main():
    print("Setting up cross-base references for SMS check-ins...")
    print(f"Main base: {MAIN_BASE_ID}")
    print(f"Check-ins base: {CHECKINS_BASE_ID}")
    
    # Step 1: Create People table in check-ins base
    people_table_id = create_people_table_in_checkins_base()
    if not people_table_id:
        print("❌ Failed to create People table. Exiting.")
        return
    
    # Step 2: Copy people from main base
    copy_people_to_checkins_base(people_table_id)
    
    print("\n✅ Cross-base reference setup complete!")
    print(f"People table ID in check-ins base: {people_table_id}")
    print("You can now update the check-ins table to reference this People table.")

if __name__ == "__main__":
    main()

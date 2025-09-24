import os
import json
import httpx
from typing import Dict, List, Optional, Any
from datetime import datetime, date
from dotenv import load_dotenv

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), '..', 'config', 'config.env'))

# Airtable configuration
AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")
AIRTABLE_PEOPLE_TABLE = os.getenv("AIRTABLE_PEOPLE_TABLE", "People")
AIRTABLE_CHECKINS_BASE_ID = os.getenv("AIRTABLE_CHECKINS_BASE_ID", AIRTABLE_BASE_ID)
AIRTABLE_CHECKINS_TABLE = os.getenv("AIRTABLE_CHECKINS_TABLE", "Check-ins")
AIRTABLE_MESSAGES_TABLE = os.getenv("AIRTABLE_MESSAGES_TABLE", "Messages")

# Add new table configurations
AIRTABLE_REMINDERS_BASE_ID = os.getenv("AIRTABLE_REMINDERS_BASE_ID", AIRTABLE_BASE_ID)
AIRTABLE_REMINDERS_MAIN_PEOPLE_TABLE = os.getenv("AIRTABLE_REMINDERS_MAIN_PEOPLE_TABLE", "People")
AIRTABLE_REMINDERS_TABLE = os.getenv("AIRTABLE_REMINDERS_TABLE", "Reminders")
AIRTABLE_NOTES_TABLE = os.getenv("AIRTABLE_NOTES_TABLE", "Notes")
AIRTABLE_FOLLOWUPS_TABLE = os.getenv("AIRTABLE_FOLLOWUPS_TABLE", "Followups")

AIRTABLE_BASE_URL = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}"
AIRTABLE_CHECKINS_BASE_URL = f"https://api.airtable.com/v0/{AIRTABLE_CHECKINS_BASE_ID}"
AIRTABLE_REMINDERS_BASE_URL = f"https://api.airtable.com/v0/{AIRTABLE_REMINDERS_BASE_ID}"

class AirtableError(Exception):
    """Custom exception for Airtable API errors"""
    pass

def _get_headers():
    """Get headers for Airtable API requests"""
    return {
        "Authorization": f"Bearer {AIRTABLE_API_KEY}",
        "Content-Type": "application/json"
    }

def _make_request(method: str, endpoint: str, data: Optional[Dict] = None, base_url: Optional[str] = None, params: Optional[Dict] = None) -> Dict:
    """Make a request to Airtable API"""
    if base_url is None:
        base_url = AIRTABLE_BASE_URL
    url = f"{base_url}/{endpoint}"
    
    async def _async_request():
        async with httpx.AsyncClient() as client:
            if method == "GET":
                response = await client.get(url, headers=_get_headers())
            elif method == "POST":
                response = await client.post(url, headers=_get_headers(), json=data)
            elif method == "PATCH":
                response = await client.patch(url, headers=_get_headers(), json=data)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            if response.status_code >= 400:
                raise AirtableError(f"Airtable API error: {response.status_code} - {response.text}")
            
            return response.json()
    
    # For now, we'll use synchronous requests with httpx
    with httpx.Client() as client:
        if method == "GET":
            response = client.get(url, headers=_get_headers(), params=params)
        elif method == "POST":
            response = client.post(url, headers=_get_headers(), json=data)
        elif method == "PATCH":
            response = client.patch(url, headers=_get_headers(), json=data)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        if response.status_code >= 400:
            raise AirtableError(f"Airtable API error: {response.status_code} - {response.text}")
        
        return response.json()

def get_person_by_phone(phone: str, prefer_checkins: bool = False) -> Optional[Dict]:
    """Get a person record by phone number"""
    try:
        # Normalize the input phone number
        normalized_phone = _normalize_phone(phone)
        
        # If prefer_checkins is True, try check-ins people table first
        if prefer_checkins:
            checkins_people_table = os.getenv("AIRTABLE_CHECKINS_PEOPLE_TABLE")
            if checkins_people_table:
                response = _make_request("GET", checkins_people_table, base_url=AIRTABLE_CHECKINS_BASE_URL)
                records = response.get("records", [])
                
                for record in records:
                    record_phone = record.get("fields", {}).get("Phone", "")
                    if record_phone:
                        # Normalize the phone number from the record
                        normalized_record_phone = _normalize_phone(record_phone)
                        if normalized_phone == normalized_record_phone:
                            return record
        
        # Try the main people table
        response = _make_request("GET", AIRTABLE_PEOPLE_TABLE)
        records = response.get("records", [])
        
        for record in records:
            record_phone = record.get("fields", {}).get("Phone", "")
            if record_phone:
                # Normalize the phone number from the record
                normalized_record_phone = _normalize_phone(record_phone)
                if normalized_phone == normalized_record_phone:
                    return record
        
        # If not found in main table and not already tried, try the check-ins people table
        if not prefer_checkins:
            checkins_people_table = os.getenv("AIRTABLE_CHECKINS_PEOPLE_TABLE")
            if checkins_people_table:
                response = _make_request("GET", checkins_people_table, base_url=AIRTABLE_CHECKINS_BASE_URL)
                records = response.get("records", [])
                
                for record in records:
                    record_phone = record.get("fields", {}).get("Phone", "")
                    if record_phone:
                        # Normalize the phone number from the record
                        normalized_record_phone = _normalize_phone(record_phone)
                        if normalized_phone == normalized_record_phone:
                            return record
        
        return None
    except Exception as e:
        print(f"Error getting person by phone {phone}: {e}")
        return None

def _normalize_phone(phone: str) -> str:
    """Normalize phone number for comparison"""
    if not phone:
        return ""
    
    # Remove all non-digit characters
    digits_only = ''.join(filter(str.isdigit, phone))
    
    # Handle different formats
    if len(digits_only) == 10:
        # Add country code
        return f"1{digits_only}"
    elif len(digits_only) == 11 and digits_only.startswith('1'):
        # Already has country code
        return digits_only
    else:
        # Return as-is if we can't normalize
        return digits_only

def update_person(person_id: str, fields: Dict[str, Any]) -> bool:
    """Update a person record with new fields"""
    try:
        data = {
            "records": [{
                "id": person_id,
                "fields": fields
            }]
        }
        
        _make_request("PATCH", AIRTABLE_PEOPLE_TABLE, data)
        return True
    except Exception as e:
        print(f"Error updating person {person_id}: {e}")
        return False

def create_person(fields: Dict[str, Any]) -> Optional[str]:
    """Create a new person record and return the person ID"""
    try:
        data = {
            "records": [{
                "fields": fields
            }]
        }
        
        response = _make_request("POST", AIRTABLE_PEOPLE_TABLE, data)
        return response["records"][0]["id"]
    except Exception as e:
        print(f"Error creating person: {e}")
        return None

def upsert_checkin(person_id: str, month: str, status: str = "Sent", 
                   pending_changes: Optional[str] = None, transcript: str = "") -> Optional[str]:
    """Create or update a check-in record"""
    try:
        # First try to find existing check-in
        filter_formula = f"{{Person}} = '{person_id}'"
        endpoint = f"{AIRTABLE_CHECKINS_TABLE}?filterByFormula={filter_formula}"
        
        response = _make_request("GET", endpoint, base_url=AIRTABLE_CHECKINS_BASE_URL)
        existing_records = response.get("records", [])
        
        checkin_data = {
            "Person": [person_id],  # Reference to person in same base
            "Status": "Sent"  # Use the available status option
        }
        
        # Note: Pending Changes field may not exist in all tables
        # if pending_changes:
        #     checkin_data["Pending Changes"] = pending_changes
        
        if existing_records:
            # Update existing check-in
            checkin_id = existing_records[0]["id"]
            data = {
                "records": [{
                    "id": checkin_id,
                    "fields": checkin_data
                }]
            }
            _make_request("PATCH", AIRTABLE_CHECKINS_TABLE, data, base_url=AIRTABLE_CHECKINS_BASE_URL)
            return checkin_id
        else:
            # Create new check-in
            data = {
                "records": [{
                    "fields": checkin_data
                }]
            }
            response = _make_request("POST", AIRTABLE_CHECKINS_TABLE, data, base_url=AIRTABLE_CHECKINS_BASE_URL)
            return response["records"][0]["id"]
            
    except Exception as e:
        print(f"Error upserting checkin for person {person_id}, month {month}: {e}")
        return None

def log_message(checkin_id: str, direction: str, from_number: str, body: str, 
                twilio_sid: str, parsed_json: Optional[str] = None) -> bool:
    """Log a message in the Messages table"""
    try:
        message_data = {
            "From": from_number,
            "Body": body
        }
        
        if parsed_json:
            message_data["Parsed JSON"] = parsed_json
        
        data = {
            "records": [{
                "fields": message_data
            }]
        }
        
        _make_request("POST", AIRTABLE_MESSAGES_TABLE, data, base_url=AIRTABLE_CHECKINS_BASE_URL)
        return True
    except Exception as e:
        print(f"Error logging message for checkin {checkin_id}: {e}")
        return False

def get_people_due_for_checkin() -> List[Dict]:
    """Get people who are due for monthly check-in"""
    try:
        # Get people with Monthly frequency who haven't been checked in recently
        # This is a simplified filter - you might want to make this more sophisticated
        filter_formula = "AND({Check-in Frequency} = 'Monthly', {Opt-out} != 1, {Consent} = 1)"
        endpoint = f"{AIRTABLE_PEOPLE_TABLE}?filterByFormula={filter_formula}"
        
        response = _make_request("GET", endpoint)
        return response.get("records", [])
    except Exception as e:
        print(f"Error getting people due for checkin: {e}")
        return []

def update_checkin_status(checkin_id: str, status: str, pending_changes: Optional[str] = None) -> bool:
    """Update check-in status and optionally pending changes"""
    try:
        fields = {"Status": status}
        if pending_changes is not None:
            fields["Pending Changes"] = pending_changes
        
        data = {
            "records": [{
                "id": checkin_id,
                "fields": fields
            }]
        }
        
        _make_request("PATCH", AIRTABLE_CHECKINS_TABLE, data, base_url=AIRTABLE_CHECKINS_BASE_URL)
        return True
    except Exception as e:
        print(f"Error updating checkin status {checkin_id}: {e}")
        return False

def append_to_transcript(checkin_id: str, message: str) -> bool:
    """Append a message to the check-in transcript"""
    try:
        # First get current transcript
        endpoint = f"{AIRTABLE_CHECKINS_TABLE}/{checkin_id}"
        response = _make_request("GET", endpoint, base_url=AIRTABLE_CHECKINS_BASE_URL)
        current_transcript = response.get("fields", {}).get("Transcript", "")
        
        # Append new message with timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        new_transcript = f"{current_transcript}\n[{timestamp}] {message}".strip()
        
        # Update the record
        data = {
            "records": [{
                "id": checkin_id,
                "fields": {"Transcript": new_transcript}
            }]
        }
        
        _make_request("PATCH", AIRTABLE_CHECKINS_TABLE, data, base_url=AIRTABLE_CHECKINS_BASE_URL)
        return True
    except Exception as e:
        print(f"Error appending to transcript for checkin {checkin_id}: {e}")
        return False

def get_all_people() -> List[Dict]:
    """Get all people from Airtable"""
    try:
        endpoint = f"{AIRTABLE_PEOPLE_TABLE}"
        response = _make_request("GET", endpoint)
        return response.get("records", [])
    except Exception as e:
        print(f"Error getting all people: {e}")
        return []

def create_reminder(reminder_data: Dict[str, Any]) -> bool:
    """Create a new reminder record in the Reminders table"""
    try:
        endpoint = f"{AIRTABLE_REMINDERS_TABLE}"
        response = _make_request("POST", endpoint, {"fields": reminder_data}, base_url=AIRTABLE_REMINDERS_BASE_URL)
        return response is not None
    except Exception as e:
        print(f"Error creating reminder: {e}")
        return False

def create_reminder_for_person(person_name: str, reminder_text: str, due_date: str = None) -> bool:
    """Create a reminder linked to a specific person"""
    try:
        # First, find the person in the main people table
        person_record = find_person_in_reminders_base(person_name)
        if not person_record:
            print(f"Person '{person_name}' not found in reminders base - DEBUG: Base={AIRTABLE_REMINDERS_BASE_ID}, Table={AIRTABLE_REMINDERS_MAIN_PEOPLE_TABLE}")
            return False
        
        # Create the reminder with link to person
        reminder_data = {
            "Reminder": reminder_text,
            "Reminders Main View": [person_record["id"]],  # Link to person record
            "Status": "Pending"  # Add status field for the scheduler
        }
        
        if due_date:
            reminder_data["Due date"] = due_date
        
        return create_reminder(reminder_data)
        
    except Exception as e:
        print(f"Error creating reminder for person: {e}")
        return False

def find_person_in_reminders_base(person_name: str) -> Optional[Dict[str, Any]]:
    """Find a person in the reminders base main people table"""
    try:
        endpoint = f"{AIRTABLE_REMINDERS_MAIN_PEOPLE_TABLE}"
        # Use case-insensitive search with LOWER() function
        params = {"filterByFormula": f"SEARCH(LOWER('{person_name.lower()}'), LOWER({{Name}}))"}
        response = _make_request("GET", endpoint, params=params, base_url=AIRTABLE_REMINDERS_BASE_URL)
        
        records = response.get("records", [])
        if records:
            return records[0]  # Return first match
        
        # If no exact match, try partial matching
        params = {"filterByFormula": f"FIND(LOWER('{person_name.lower()}'), LOWER({{Name}}))"}
        response = _make_request("GET", endpoint, params=params, base_url=AIRTABLE_REMINDERS_BASE_URL)
        
        records = response.get("records", [])
        if records:
            return records[0]  # Return first match
            
        return None
        
    except Exception as e:
        print(f"Error finding person in reminders base: {e}")
        return None

def create_note(note_data: Dict[str, Any]) -> bool:
    """Create a new note record in the Notes table"""
    try:
        endpoint = f"{AIRTABLE_NOTES_TABLE}"
        response = _make_request("POST", endpoint, {"fields": note_data})
        return response is not None
    except Exception as e:
        print(f"Error creating note: {e}")
        return False

def create_followup(followup_data: Dict[str, Any]) -> bool:
    """Create a new follow-up record in the Followups table"""
    try:
        endpoint = f"{AIRTABLE_FOLLOWUPS_TABLE}"
        response = _make_request("POST", endpoint, {"fields": followup_data})
        return response is not None
    except Exception as e:
        print(f"Error creating followup: {e}")
        return False

def get_reminders_for_person(person_id: str) -> List[Dict[str, Any]]:
    """Get all reminders for a specific person"""
    try:
        endpoint = f"{AIRTABLE_REMINDERS_TABLE}"
        params = {"filterByFormula": f"{{Person}} = '{person_id}'"}
        response = _make_request("GET", endpoint, params=params, base_url=AIRTABLE_REMINDERS_BASE_URL)
        return response.get("records", [])
    except Exception as e:
        print(f"Error getting reminders for person: {e}")
        return []

def get_notes_for_person(person_id: str) -> List[Dict[str, Any]]:
    """Get all notes for a specific person"""
    try:
        endpoint = f"{AIRTABLE_NOTES_TABLE}"
        params = {"filterByFormula": f"{{Person}} = '{person_id}'"}
        response = _make_request("GET", endpoint, params=params)
        return response.get("records", [])
    except Exception as e:
        print(f"Error getting notes for person: {e}")
        return []

def get_followups_for_person(person_id: str) -> List[Dict[str, Any]]:
    """Get all follow-ups for a specific person"""
    try:
        endpoint = f"{AIRTABLE_FOLLOWUPS_TABLE}"
        params = {"filterByFormula": f"{{Person}} = '{person_id}'"}
        response = _make_request("GET", endpoint, params=params)
        return response.get("records", [])
    except Exception as e:
        print(f"Error getting followups for person: {e}")
        return []

def update_reminder_status(reminder_id: str, status: str, completed_at: Optional[str] = None) -> bool:
    """Update the status of a reminder"""
    try:
        updates = {"Status": status}
        if completed_at:
            updates["Completed At"] = completed_at
        
        endpoint = f"{AIRTABLE_REMINDERS_TABLE}/{reminder_id}"
        response = _make_request("PATCH", endpoint, {"fields": updates}, base_url=AIRTABLE_REMINDERS_BASE_URL)
        return response is not None
    except Exception as e:
        print(f"Error updating reminder status: {e}")
        return False

def update_followup_status(followup_id: str, status: str, completed_at: Optional[str] = None) -> bool:
    """Update the status of a follow-up"""
    try:
        updates = {"Status": status}
        if completed_at:
            updates["Completed At"] = completed_at
        
        endpoint = f"{AIRTABLE_FOLLOWUPS_TABLE}/{followup_id}"
        response = _make_request("PATCH", endpoint, {"fields": updates})
        return response is not None
    except Exception as e:
        print(f"Error updating followup status: {e}")
        return False

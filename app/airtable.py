import os
import json
import httpx
from typing import Dict, List, Optional, Any
from datetime import datetime, date

# Airtable configuration
AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")
AIRTABLE_PEOPLE_TABLE = os.getenv("AIRTABLE_PEOPLE_TABLE", "People")
AIRTABLE_CHECKINS_TABLE = os.getenv("AIRTABLE_CHECKINS_TABLE", "Check-ins")
AIRTABLE_MESSAGES_TABLE = os.getenv("AIRTABLE_MESSAGES_TABLE", "Messages")

AIRTABLE_BASE_URL = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}"

class AirtableError(Exception):
    """Custom exception for Airtable API errors"""
    pass

def _get_headers():
    """Get headers for Airtable API requests"""
    return {
        "Authorization": f"Bearer {AIRTABLE_API_KEY}",
        "Content-Type": "application/json"
    }

def _make_request(method: str, endpoint: str, data: Optional[Dict] = None) -> Dict:
    """Make a request to Airtable API"""
    url = f"{AIRTABLE_BASE_URL}/{endpoint}"
    
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
            response = client.get(url, headers=_get_headers())
        elif method == "POST":
            response = client.post(url, headers=_get_headers(), json=data)
        elif method == "PATCH":
            response = client.patch(url, headers=_get_headers(), json=data)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        if response.status_code >= 400:
            raise AirtableError(f"Airtable API error: {response.status_code} - {response.text}")
        
        return response.json()

def get_person_by_phone(phone: str) -> Optional[Dict]:
    """Get a person record by phone number"""
    try:
        # Airtable filter formula to find person by phone
        filter_formula = f"{{Phone}} = '{phone}'"
        endpoint = f"{AIRTABLE_PEOPLE_TABLE}?filterByFormula={filter_formula}"
        
        response = _make_request("GET", endpoint)
        records = response.get("records", [])
        
        if records:
            return records[0]
        return None
    except Exception as e:
        print(f"Error getting person by phone {phone}: {e}")
        return None

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

def upsert_checkin(person_id: str, month: str, status: str = "Sent", 
                   pending_changes: Optional[str] = None, transcript: str = "") -> Optional[str]:
    """Create or update a check-in record"""
    try:
        # First try to find existing check-in
        filter_formula = f"AND({{Person}} = '{person_id}', {{Month}} = '{month}')"
        endpoint = f"{AIRTABLE_CHECKINS_TABLE}?filterByFormula={filter_formula}"
        
        response = _make_request("GET", endpoint)
        existing_records = response.get("records", [])
        
        checkin_data = {
            "Person": [person_id],
            "Month": month,
            "Status": status,
            "Transcript": transcript,
            "Last Message At": datetime.now().isoformat()
        }
        
        if pending_changes:
            checkin_data["Pending Changes"] = pending_changes
        
        if existing_records:
            # Update existing check-in
            checkin_id = existing_records[0]["id"]
            data = {
                "records": [{
                    "id": checkin_id,
                    "fields": checkin_data
                }]
            }
            _make_request("PATCH", AIRTABLE_CHECKINS_TABLE, data)
            return checkin_id
        else:
            # Create new check-in
            data = {
                "records": [{
                    "fields": checkin_data
                }]
            }
            response = _make_request("POST", AIRTABLE_CHECKINS_TABLE, data)
            return response["records"][0]["id"]
            
    except Exception as e:
        print(f"Error upserting checkin for person {person_id}, month {month}: {e}")
        return None

def log_message(checkin_id: str, direction: str, from_number: str, body: str, 
                twilio_sid: str, parsed_json: Optional[str] = None) -> bool:
    """Log a message in the Messages table"""
    try:
        message_data = {
            "Check-in": [checkin_id],
            "When": datetime.now().isoformat(),
            "Direction": direction,
            "From": from_number,
            "Body": body,
            "Twilio SID": twilio_sid
        }
        
        if parsed_json:
            message_data["Parsed JSON"] = parsed_json
        
        data = {
            "records": [{
                "fields": message_data
            }]
        }
        
        _make_request("POST", AIRTABLE_MESSAGES_TABLE, data)
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
        
        _make_request("PATCH", AIRTABLE_CHECKINS_TABLE, data)
        return True
    except Exception as e:
        print(f"Error updating checkin status {checkin_id}: {e}")
        return False

def append_to_transcript(checkin_id: str, message: str) -> bool:
    """Append a message to the check-in transcript"""
    try:
        # First get current transcript
        endpoint = f"{AIRTABLE_CHECKINS_TABLE}/{checkin_id}"
        response = _make_request("GET", endpoint)
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
        
        _make_request("PATCH", AIRTABLE_CHECKINS_TABLE, data)
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

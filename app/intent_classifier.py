import os
import json
from typing import Dict, Any, Optional
import openai

# OpenAI configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

# Intent classification schema
INTENT_CLASSIFICATION_SCHEMA = {
    "type": "object",
    "properties": {
        "intent": {
            "type": "string",
            "enum": [
                "update_person_info",    # Updates to People table (birthday, company, role, city)
                "manage_tags",           # Tag operations (add/remove tags)
                "create_reminder",       # Create reminders/tasks
                "create_note",           # Add notes or comments
                "schedule_followup",     # Schedule future check-ins
                "no_change",             # No updates needed
                "confirm_changes",       # Confirm previously proposed changes
                "opt_out",               # Unsubscribe
                "unclear"                # Fallback for ambiguous messages
            ]
        },
        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
        "target_table": {
            "type": "string",
            "enum": ["Core People", "SMS Check-ins - From Core", "None"]
        },
        "extracted_data": {
            "type": "object",
            "properties": {
                "target_person": {"type": "string"},
                "field_updates": {"type": "object"},
                "tags_to_add": {"type": "array", "items": {"type": "string"}},
                "tags_to_remove": {"type": "array", "items": {"type": "string"}},
                "reminder_action": {"type": "string"},
                "reminder_timeline": {"type": "string"},
                "reminder_priority": {"type": "string", "enum": ["low", "medium", "high"]},
                "note_content": {"type": "string"},
                "followup_timeline": {"type": "string"},
                "followup_reason": {"type": "string"}
            }
        }
    },
    "required": ["intent", "confidence", "target_table", "extracted_data"]
}

def classify_intent(message: str, person_context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Classify the intent of an SMS message and determine target Airtable table
    
    Args:
        message: Raw SMS text from user
        person_context: Current person's data for context
        
    Returns:
        Dictionary with intent classification, target table, and extracted data
    """
    if not OPENAI_API_KEY:
        print("OpenAI API key not configured")
        return _fallback_classification(message)
    
    try:
        client = openai.OpenAI(api_key=OPENAI_API_KEY)
        
        system_prompt = f"""You are an intent classifier for SMS messages about people management and relationship tracking.

Current person context: {json.dumps(person_context, indent=2)}

Classify the user's intent and determine which Airtable table should be updated from this message: "{message}"

Available intents and their target tables:
- update_person_info → Core People table: Updates to personal info (birthday, company/role stored in How We Met field, location stored in How We Met field)
- manage_tags → Core People table: Adding or removing tags (General Tag, Location Tag, Community Tag, Communication Tag)
- create_reminder → SMS Check-ins - From Core table: Creating a reminder/task for future action
- create_note → Core People table: Adding notes (stored in How We Met field)
- schedule_followup → SMS Check-ins - From Core table: Scheduling future check-ins or meetings
- no_change → None: Confirming no updates needed
- confirm_changes → None: Confirming previously proposed changes
- opt_out → Core People table: Unsubscribing from messages
- unclear → None: Message is ambiguous or doesn't fit other categories

Note: LinkedIn table is read-only (auto-populated from LinkedIn), so company/role updates are stored in Core People "How We Met" field.

Extract relevant data based on the intent:
- For update_person_info: extract field_updates with specific fields to change (birthday, company, role, location)
- For manage_tags: extract tags_to_add and/or tags_to_remove arrays, and determine which tag field (General Tag, Location Tag, etc.)
- For create_reminder: extract reminder_action, reminder_timeline, and reminder_priority
- For create_note: extract note_content
- For schedule_followup: extract followup_timeline and followup_reason

Return a JSON object with the intent, confidence (0-1), target_table, and extracted_data."""

        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[{"role": "system", "content": system_prompt}],
            response_format={"type": "json_object"},
            temperature=0.1,
            max_tokens=500
        )
        
        content = response.choices[0].message.content
        result = json.loads(content)
        
        # Validate the result
        if not all(key in result for key in ["intent", "confidence", "target_table", "extracted_data"]):
            return _fallback_classification(message)
        
        return result
        
    except Exception as e:
        print(f"Error in intent classification: {e}")
        return _fallback_classification(message)

def _fallback_classification(message: str) -> Dict[str, Any]:
    """
    Fallback classification using simple keyword matching
    """
    message_lower = message.lower()
    
    # Simple keyword-based classification
    if any(word in message_lower for word in ["birthday", "born", "birth"]):
        return {
            "intent": "update_person_info",
            "confidence": 0.7,
            "target_table": "Core People",
            "extracted_data": {"field_updates": {"birthday": _extract_birthday(message)}}
        }
    elif any(word in message_lower for word in ["tag", "label", "categorize"]):
        return {
            "intent": "manage_tags",
            "confidence": 0.6,
            "target_table": "Core People",
            "extracted_data": {"tags_to_add": _extract_tags(message)}
        }
    elif any(word in message_lower for word in ["remind", "reminder", "follow up", "reach out"]):
        return {
            "intent": "create_reminder",
            "confidence": 0.6,
            "target_table": "SMS Check-ins - From Core",
            "extracted_data": {
                "reminder_action": message,
                "reminder_timeline": "unspecified",
                "reminder_priority": "medium"
            }
        }
    elif any(word in message_lower for word in ["note", "comment", "observe"]):
        return {
            "intent": "create_note",
            "confidence": 0.6,
            "target_table": "Core People",
            "extracted_data": {"note_content": message}
        }
    else:
        return {
            "intent": "unclear",
            "confidence": 0.3,
            "target_table": "None",
            "extracted_data": {}
        }

def _extract_birthday(message: str) -> str:
    """Extract birthday from message using regex"""
    import re
    # Look for MM/DD/YYYY or MM-DD-YYYY patterns
    birthday_pattern = r'(\d{1,2}[/-]\d{1,2}[/-]\d{4})'
    match = re.search(birthday_pattern, message)
    if match:
        return match.group(1)
    return ""

def _extract_tags(message: str) -> list:
    """Extract tags from message"""
    import re
    # Look for quoted strings or words after "tag" or "with"
    tag_patterns = [
        r'tag\s+\w+\s+with\s+["\']([^"\']+)["\']',
        r'tag\s+\w+\s+with\s+(\w+)',
        r'["\']([^"\']+)["\']'
    ]
    
    tags = []
    for pattern in tag_patterns:
        matches = re.findall(pattern, message, re.IGNORECASE)
        tags.extend(matches)
    
    return list(set(tags))  # Remove duplicates
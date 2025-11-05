"""
Intent Classifier Module

This module classifies SMS messages into different intents using OpenAI's API.
"""

import os
import json
from typing import Dict, Any, Optional
import openai
from dotenv import load_dotenv

# Load environment variables from config file
load_dotenv('config/config.env')

# =============================================================================
# CONFIGURATION
# =============================================================================

# OpenAI configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

# =============================================================================
# INTENT CLASSIFICATION SCHEMA
# =============================================================================

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
                "new_friend",            # Create new friend/person
                "no_change",             # No updates needed
                "confirm_changes",       # Confirm previously proposed changes
                "opt_out",               # Unsubscribe
                "unclear"                # Fallback for ambiguous messages
            ]
        },
        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
        "target_table": {
            "type": "string",
            "enum": ["Core People", "SMS Check-ins - From Core", "Reminders", "None"]
        },
        "extracted_data": {
            "type": "object",
            "properties": {
                "target_person": {"type": "string"},
                "target_person_name": {"type": "string"},
                "field_updates": {"type": "object"},
                "tags_to_add": {"type": "array", "items": {"type": "string"}},
                "tags_to_remove": {"type": "array", "items": {"type": "string"}},
                "reminder_action": {"type": "string"},
                "reminder_timeline": {"type": "string"},
                "reminder_priority": {"type": "string", "enum": ["low", "medium", "high"]},
                "note_content": {"type": "string"},
                "followup_timeline": {"type": "string"},
                "followup_reason": {"type": "string"},
                "friend_name": {"type": "string"},
                "query_type": {"type": "string"},
                "query_terms": {"type": "array", "items": {"type": "string"}}
            }
        }
    },
    "required": ["intent", "confidence", "target_table", "extracted_data"]
}

# =============================================================================
# MAIN CLASSIFICATION FUNCTIONS
# =============================================================================

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
        return {
            "intent": "unclear",
            "confidence": 0.0,
            "target_table": "None",
            "extracted_data": {
                "error_message": "OpenAI API key not configured"
            }
        }
    
    try:
        client = openai.OpenAI(api_key=OPENAI_API_KEY)
        
        system_prompt = f"""You are an intent classifier for SMS messages about people management and relationship tracking.

Current person context: {json.dumps(person_context, indent=2)}

Classify the user's intent and determine which Airtable table should be updated from this message: "{message}"

IMPORTANT: This system is ONLY used to update OTHER PEOPLE'S data, never the texter's own data. The texter is always updating someone else's information.

Available intents and their target tables:
- update_person_info → Core People table: Updates to personal info (birthday, company/role stored in How We Met field, location stored in How We Met field)
- manage_tags → Core People table: Adding or removing tags (General Tag, Location Tag, Community Tag, Communication Tag)
- create_reminder → Reminders table: Creating a reminder/task for future action
- create_note → Core People table: Adding notes (stored in How We Met field)
- schedule_followup → SMS Check-ins - From Core table: Scheduling future check-ins or meetings
- new_friend → Core People table: Creating a new friend/person record
- query_data → Multiple tables: Querying information from Airtables (people, reminders, notes, etc.)
- no_change → None: Confirming no updates needed
- confirm_changes → None: Confirming previously proposed changes
- opt_out → Core People table: Unsubscribing from messages
- unclear → None: Message is ambiguous or doesn't fit other categories

Note: LinkedIn table is read-only (auto-populated from LinkedIn), so company/role updates are stored in Core People "How We Met" field.

Extract relevant data based on the intent:
- For update_person_info: ALWAYS extract target_person_name (the person whose info is being updated) AND field_updates with specific fields to change (birthday, company, role, location). NEVER use the current person context - the texter is always updating someone else's data. If no specific person is mentioned, classify as "unclear". Examples: "update John's birthday to 3/14/1999", "change Sarah's company to Tech Corp"
- For manage_tags: extract target_person_name (the person whose tags are being updated) AND tags_to_add and/or tags_to_remove arrays. NEVER use the current person context - the texter is always updating someone else's tags. If no specific person is mentioned, classify as "unclear". Examples: "tag John with mentor", "remove developer tag from Sarah"
- For create_reminder: extract reminder_action, reminder_timeline, and reminder_priority. If the action mentions a specific person, extract target_person_name. Examples: "remind me to call John tomorrow" → target_person_name: "John"
- For create_note: extract target_person_name (the person the note is about) AND note_content. NEVER use the current person context - the texter is always adding notes about someone else. If no specific person is mentioned, classify as "unclear". Examples: "add a note to John about crypto interest", "note: Sarah mentioned PM role"
- For schedule_followup: extract target_person_name (who to follow up with) AND followup_timeline and followup_reason. NEVER use the current person context - the texter is always scheduling follow-ups with someone else. If no specific person is mentioned, classify as "unclear". Examples: "follow up with John next week", "schedule follow-up with Sarah about project"
- For new_friend: ALWAYS extract friend_name as the complete name of the person to add. Extract the full name even from partial messages. Examples: "new friend John Smith" → friend_name: "John Smith", "add Jen H" → friend_name: "Jen H", "met Sarah Johnson" → friend_name: "Sarah Johnson", "introduce Mike Wilson" → friend_name: "Mike Wilson", "add David" → friend_name: "David". The friend_name should be the complete name of the person being added, extracted from the message text. If the message contains phrases like "new friend", "add", "met", "introduce", or similar, extract the person's name that follows.
- For query_data: extract query_type (people, reminders, notes, checkins, etc.) and query_terms as an ARRAY of strings (person names, keywords, etc.). Examples: "Is David Kobrosky in here" → query_terms: ["David Kobrosky"], "Do I have any reminders about David?" → query_terms: ["David"], "What notes do I have about Sarah?" → query_terms: ["Sarah"]

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
            return {
                "intent": "unclear",
                "confidence": 0.0,
                "target_table": "None",
                "extracted_data": {
                    "error_message": "Invalid response format from OpenAI"
                }
            }
        
        return result
        
    except Exception as e:
        print(f"Error in intent classification: {e}")
        return {
            "intent": "unclear",
            "confidence": 0.0,
            "target_table": "None",
            "extracted_data": {
                "error_message": f"OpenAI classification error: {str(e)}"
            }
        }

# =============================================================================
# NAME MATCHING
# =============================================================================

def match_name_to_person(query_name: str, person_names: list) -> Optional[str]:
    """
    Use AI to match a query name to the best matching person name from a list.
    Handles partial names, abbreviations, and variations.
    
    Args:
        query_name: The name being searched for (e.g., "Jen H")
        person_names: List of full person names to match against (e.g., ["Jen H Smith", "John Doe"])
        
    Returns:
        The best matching person name, or None if no good match
    """
    if not OPENAI_API_KEY or not person_names:
        return None
    
    if not query_name:
        return None
    
    try:
        client = openai.OpenAI(api_key=OPENAI_API_KEY)
        
        prompt = f"""You are a name matching system. Match the query name to the best matching person from the list.

Query name: "{query_name}"
Available person names: {json.dumps(person_names, indent=2)}

Rules:
- Match partial names (e.g., "Jen H" should match "Jen H Smith")
- Match abbreviations (e.g., "Jen H" should match "Jennifer H. Smith")
- Match nicknames and variations
- Only return a match if you're confident (confidence > 0.7)
- Return the EXACT name from the list if there's a match
- Return null if no good match exists

Return a JSON object with:
- "match": the matched person name (exact from list) or null
- "confidence": 0.0 to 1.0
- "reason": brief explanation of why this match was chosen"""
        
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.1,
            max_tokens=200
        )
        
        content = response.choices[0].message.content
        result = json.loads(content)
        
        match = result.get("match")
        confidence = result.get("confidence", 0.0)
        
        if match and confidence > 0.7:
            return match
        else:
            return None
            
    except Exception as e:
        print(f"Error in AI name matching: {e}")
        return None

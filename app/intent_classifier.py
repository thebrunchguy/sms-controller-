"""
Intent Classifier Module

This module classifies SMS messages into different intents using OpenAI's API
and provides fallback regex-based classification when the API is unavailable.
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
    # Check for self-referential terms or missing person names that should be rejected immediately
    message_lower = message.lower()
    if any(word in message_lower for word in ["birthday", "born", "birth"]):
        # Check for self-referential terms
        if any(word in message_lower for word in ["my", "mine", "i am", "i'm"]):
            return {
                "intent": "unclear",
                "confidence": 0.3,
                "extracted_data": {
                    "error_message": "❌ Please specify whose birthday you want to update. For example: 'update John's birthday to 3/14/1999'"
                }
            }
        
        # Check for messages without explicit person names
        person_name = _extract_person_name_from_birthday_update(message)
        if not person_name:
            return {
                "intent": "unclear",
                "confidence": 0.3,
                "extracted_data": {
                    "error_message": "❌ Please specify whose birthday you want to update. For example: 'update John's birthday to 3/14/1999'"
                }
            }
    
    if not OPENAI_API_KEY:
        print("OpenAI API key not configured")
        return _fallback_classification(message)
    
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
- For manage_tags: extract tags_to_add and/or tags_to_remove arrays, and determine which tag field (General Tag, Location Tag, etc.)
- For create_reminder: extract reminder_action, reminder_timeline, and reminder_priority
- For create_note: extract note_content
- For schedule_followup: extract followup_timeline and followup_reason
- For new_friend: extract friend_name from messages like "new friend John Smith", "met Sarah Johnson", "introduce Mike Wilson"
- For query_data: extract query_type (people, reminders, notes, checkins, etc.) and query_terms (person names, keywords, etc.). Examples: "Is David Kobrosky in here", "Do I have any reminders about David?", "What notes do I have about Sarah?"

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

# =============================================================================
# FALLBACK CLASSIFICATION
# =============================================================================

def _fallback_classification(message: str) -> Dict[str, Any]:
    """
    Fallback classification using simple keyword matching
    """
    message_lower = message.lower().strip()
    
    # Check for greetings and casual conversation first
    greeting_words = ["hello", "hi", "hey", "how are you", "what's up", "good morning", "good afternoon", "good evening"]
    if any(word in message_lower for word in greeting_words):
        return {
            "intent": "unclear",
            "confidence": 0.3,
            "target_table": "None",
            "extracted_data": {
                "error_message": "Hello! I'm here to help you manage your information. You can ask me to 'remind you to...', 'update your...', or 'add a note...'. What would you like me to help you with?"
            }
        }
    
    # Check for questions
    question_words = ["what", "how", "when", "where", "why", "can you", "do you", "are you"]
    if any(word in message_lower for word in question_words):
        return {
            "intent": "unclear",
            "confidence": 0.3,
            "target_table": "None",
            "extracted_data": {
                "error_message": "I'm designed to help you manage your information and reminders. You can ask me to 'remind you to...', 'update your...', or 'add a note...'. What specific action would you like me to help you with?"
            }
        }
    
    # Simple keyword-based classification for actionable intents
    if any(word in message_lower for word in ["new friend", "met", "introduce"]):
        friend_name = _extract_friend_name(message)
        return {
            "intent": "new_friend",
            "confidence": 0.8,
            "target_table": "Core People",
            "extracted_data": {"friend_name": friend_name}
        }
    elif any(word in message_lower for word in ["birthday", "born", "birth"]):
        # Check for explicit person names first
        person_name = _extract_person_name_from_birthday_update(message)
        
        # Also check for "my" or other self-referential terms that should be rejected
        if any(word in message_lower for word in ["my", "mine", "i am", "i'm"]):
            return {
                "intent": "unclear",
                "confidence": 0.3,
                "extracted_data": {
                    "error_message": "❌ Please specify whose birthday you want to update. For example: 'update John's birthday to 3/14/1999'"
                }
            }
        
        if not person_name:
            return {
                "intent": "unclear",
                "confidence": 0.3,
                "extracted_data": {
                    "error_message": "❌ Please specify whose birthday you want to update. For example: 'update John's birthday to 3/14/1999'"
                }
            }
        return {
            "intent": "update_person_info",
            "confidence": 0.7,
            "target_table": "Core People",
            "extracted_data": {
                "field_updates": {"birthday": _extract_birthday(message)},
                "target_person_name": person_name
            }
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
                "reminder_timeline": _extract_timeline(message),
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
    elif any(word in message_lower for word in ["is", "do i have", "what", "show me", "find", "search", "look for", "tell me about"]):
        # Extract query type and terms
        query_type = "people"  # default
        query_terms = []
        
        # Determine query type based on keywords
        if any(word in message_lower for word in ["reminder", "remind"]):
            query_type = "reminders"
        elif any(word in message_lower for word in ["note", "notes"]):
            query_type = "notes"
        elif any(word in message_lower for word in ["checkin", "check-in", "check in"]):
            query_type = "checkins"
        
        # Extract person names or keywords
        import re
        # Look for capitalized words that might be names
        name_pattern = r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b'
        matches = re.findall(name_pattern, message)
        query_terms = [match for match in matches if match.lower() not in ['is', 'do', 'have', 'what', 'show', 'me', 'find', 'search', 'look', 'for', 'tell', 'about', 'any', 'the', 'a', 'an']]
        
        return {
            "intent": "query_data",
            "confidence": 0.7,
            "target_table": "Multiple",
            "extracted_data": {
                "query_type": query_type,
                "query_terms": query_terms
            }
        }
    else:
        return {
            "intent": "unclear",
            "confidence": 0.3,
            "target_table": "None",
            "extracted_data": {
                "error_message": "I couldn't understand what you'd like me to do. Please try rephrasing your message with specific actions like 'remind me to...', 'update my...', or 'add a note...'"
            }
        }

# =============================================================================
# EXTRACTION HELPER FUNCTIONS
# =============================================================================

def _extract_timeline(message: str) -> str:
    """Extract timeline from message using the comprehensive timeline extractor"""
    try:
        from .timeline_extractor import extract_timeline
        return extract_timeline(message)
    except ImportError:
        # Fallback to simple extraction if timeline_extractor is not available
        import re
        message_lower = message.lower()
        
        # Common timeline patterns
        timeline_patterns = [
            r'(next\s+week)',
            r'(next\s+month)',
            r'(next\s+year)',
            r'(tomorrow)',
            r'(in\s+a\s+few\s+days)',
            r'(in\s+a\s+couple\s+days)',
            r'(in\s+a\s+few\s+weeks)',
            r'(in\s+a\s+couple\s+weeks)',
            r'(in\s+a\s+few\s+months)',
            r'(in\s+a\s+couple\s+months)',
            r'(in\s+\d+\s+days?)',
            r'(in\s+\d+\s+weeks?)',
            r'(in\s+\d+\s+months?)',
            r'(this\s+week)',
            r'(this\s+month)',
            r'(this\s+year)'
        ]
        
        for pattern in timeline_patterns:
            match = re.search(pattern, message_lower)
            if match:
                return match.group(1)
        
        return "unspecified"

def _extract_birthday(message: str) -> str:
    """Extract birthday from message using regex"""
    import re
    # Look for MM/DD/YYYY or MM-DD-YYYY patterns
    birthday_pattern = r'(\d{1,2}[/-]\d{1,2}[/-]\d{4})'
    match = re.search(birthday_pattern, message)
    if match:
        return match.group(1)
    return ""

def _extract_friend_name(message: str) -> str:
    """Extract friend name from 'new friend' messages"""
    import re
    
    # Pattern for "new friend [Name]" or "met [Name]" or "introduce [Name]"
    patterns = [
        r'new\s+friend\s+(.+)',
        r'met\s+(.+)',
        r'introduce\s+(.+)'
    ]
    
    message_lower = message.lower()
    for pattern in patterns:
        match = re.search(pattern, message_lower)
        if match:
            name = match.group(1).strip()
            # Clean up the name (remove extra words, capitalize properly)
            name_parts = name.split()
            if name_parts:
                return ' '.join([part.capitalize() for part in name_parts])
    
    return ""

def _extract_person_name_from_birthday_update(message: str) -> str:
    """Extract person name from birthday update messages"""
    import re
    
    # Patterns for birthday update messages
    patterns = [
        # "update [Name]'s birthday to [date]"
        r'update\s+([A-Za-z\s]+?)\'s\s+birthday',
        # "change [Name]'s birthday to [date]"
        r'change\s+([A-Za-z\s]+?)\'s\s+birthday',
        # "set [Name]'s birthday to [date]"
        r'set\s+([A-Za-z\s]+?)\'s\s+birthday',
        # "[Name]'s birthday is [date]"
        r'([A-Za-z\s]+?)\'s\s+birthday\s+is',
        # "birthday for [Name] is [date]"
        r'birthday\s+for\s+([A-Za-z\s]+?)\s+is',
        # "update [Name] birthday [date]"
        r'update\s+([A-Za-z\s]+?)\s+birthday\s+(?:to\s+)?',
        # "change [Name] birthday [date]"
        r'change\s+([A-Za-z\s]+?)\s+birthday\s+(?:to\s+)?',
    ]
    
    message_lower = message.lower()
    for pattern in patterns:
        match = re.search(pattern, message_lower)
        if match:
            name = match.group(1).strip()
            # Clean up the name (remove extra words, capitalize properly)
            name_parts = name.split()
            if name_parts:
                return ' '.join([part.capitalize() for part in name_parts])
    
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
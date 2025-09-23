from typing import Dict, Any, Tuple, Optional
from . import airtable
from . import twilio_utils
from datetime import datetime, timedelta
import re
import json

class IntentHandlers:
    
    @staticmethod
    def handle_update_person_info(
        extracted_data: Dict[str, Any], 
        person_id: str, 
        person_fields: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """Handle updates to Core People table (Birthday, How We Met, etc.)"""
        
        field_updates = extracted_data.get("field_updates", {})
        
        # Map and validate field updates for Core People table
        updates = {}
        
        # Birthday updates
        if "birthday" in field_updates:
            birthday = _normalize_birthday(field_updates["birthday"])
            if birthday:
                updates["Birthday"] = birthday
        
        # Store company/role updates in How We Met field since LinkedIn table is read-only
        if "company" in field_updates or "role" in field_updates:
            current_how_we_met = person_fields.get("How We Met", "")
            new_info = []
            
            if current_how_we_met and current_how_we_met != "N/A":
                new_info.append(current_how_we_met)
            
            if "company" in field_updates:
                new_info.append(f"Company: {field_updates['company']}")
            
            if "role" in field_updates:
                new_info.append(f"Role: {field_updates['role']}")
            
            updates["How We Met"] = " | ".join(new_info)
        
        # Location updates (store in How We Met since we don't have a direct location field)
        if "location" in field_updates or "city" in field_updates:
            location = field_updates.get("location") or field_updates.get("city")
            current_how_we_met = person_fields.get("How We Met", "")
            
            if current_how_we_met and current_how_we_met != "N/A":
                updates["How We Met"] = f"{current_how_we_met} | Location: {location}"
            else:
                updates["How We Met"] = f"Location: {location}"
        
        if updates:
            # Find the person in the main people table by name and email
            # since person_id is from check-ins table
            person_name = person_fields.get("Name", "")
            person_email = person_fields.get("Email", "")
            
            # Get all people from main table and find matching record
            main_people = airtable.get_all_people()
            main_person_id = None
            
            for person in main_people:
                fields = person.get("fields", {})
                if (fields.get("Name") == person_name and 
                    fields.get("Email") == person_email):
                    main_person_id = person["id"]
                    break
            
            if not main_person_id:
                return False, "❌ I couldn't find your profile in the main system to update. This might be due to a name or email mismatch. Please contact support if this continues."
            
            success = airtable.update_person(main_person_id, updates)
            if success:
                updated_fields = list(updates.keys())
                return True, f"✅ Updated {', '.join(updated_fields)} in your profile"
            else:
                return False, "❌ I couldn't update your information in the system. This might be due to a connection issue. Please try again or contact support if the problem persists."
        
        return False, "❌ I couldn't determine what information you'd like me to update. Please be specific, like 'update my birthday to 03/14/1999' or 'update my company to Tech Corp'"
    
    @staticmethod
    def handle_manage_tags(
        extracted_data: Dict[str, Any], 
        person_id: str, 
        person_fields: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """Handle tag operations - updates People table Tags field"""
        
        tags_to_add = extracted_data.get("tags_to_add", [])
        tags_to_remove = extracted_data.get("tags_to_remove", [])
        
        if not tags_to_add and not tags_to_remove:
            return False, "❌ I couldn't determine which tags you'd like to add or remove. Please be specific, like 'tag me with mentor' or 'remove the developer tag'"
        
        # Get current tags from People table
        current_tags = person_fields.get("Tags", [])
        
        # Add new tags
        if tags_to_add:
            current_tags.extend(tags_to_add)
        
        # Remove specified tags
        if tags_to_remove:
            current_tags = [tag for tag in current_tags if tag not in tags_to_remove]
        
        # Remove duplicates
        current_tags = list(set(current_tags))
        
        success = airtable.update_person(person_id, {"Tags": current_tags})
        
        if success:
            messages = []
            if tags_to_add:
                messages.append(f"Added: {', '.join(tags_to_add)}")
            if tags_to_remove:
                messages.append(f"Removed: {', '.join(tags_to_remove)}")
            return True, f"✅ Tags updated - {', '.join(messages)}"
        else:
            return False, "❌ I couldn't update your tags in the system. This might be due to a connection issue. Please try again or contact support if the problem persists."
    
    @staticmethod
    def handle_create_reminder(
        extracted_data: Dict[str, Any], 
        person_id: str, 
        person_fields: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """Handle creating reminders in Reminders table"""
        
        action = extracted_data.get("reminder_action", "")
        timeline = extracted_data.get("reminder_timeline", "")
        priority = extracted_data.get("reminder_priority", "medium")
        
        if not action:
            return False, "❌ I couldn't determine what you'd like me to remind you about. Please be more specific, like 'remind me to call John' or 'remind me to follow up on the project'"
        
        # Determine target person's name
        # Prefer explicit target from classifier if present
        person_name = extracted_data.get("target_person") or _extract_person_name_from_action(action, person_fields)

        # Guard against missing/invalid person name
        if not person_name or str(person_name).strip().lower() in ["none", "unknown"]:
            return False, "❌ I couldn't determine who you'd like this reminder to involve. Please specify a name, like 'remind me to text John Doe today'."
        
        # Calculate due date based on timeline using the new extractor
        try:
            from .timeline_extractor import parse_timeline_to_datetime
            due_date = parse_timeline_to_datetime(timeline)
        except ImportError:
            # Fallback to old method
            due_date = _parse_timeline_to_date(timeline)
        
        due_date_str = due_date.strftime("%Y-%m-%d %H:%M:%S") if due_date else None
        
        # Create reminder using the new function that links to person
        success = airtable.create_reminder_for_person(
            person_name=person_name,
            reminder_text=action,
            due_date=due_date_str
        )
        
        if success:
            due_text = f" (due: {timeline})" if timeline else ""
            return True, f"✅ Reminder created: {action}{due_text}"
        else:
            return False, "❌ I couldn't create the reminder in your system. This might be due to a connection issue or missing information. Please try again or contact support if the problem persists."
    
    @staticmethod
    def handle_create_note(
        extracted_data: Dict[str, Any], 
        person_id: str, 
        person_fields: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """Handle creating notes in Notes table"""
        
        note_content = extracted_data.get("note_content", "")
        
        if not note_content:
            return False, "❌ I couldn't determine what note you'd like me to add. Please be more specific, like 'note: John mentioned he's interested in the PM role'"
        
        # Create note record
        note_data = {
            "Person": [person_id],
            "Content": note_content,
            "Type": "SMS Note",
            "Created At": datetime.now().isoformat(),
            "Created By": "SMS"
        }
        
        success = airtable.create_note(note_data)
        
        if success:
            return True, f"✅ Note added: {note_content[:50]}{'...' if len(note_content) > 50 else ''}"
        else:
            return False, "❌ I couldn't save the note to your system. This might be due to a connection issue. Please try again or contact support if the problem persists."
    
    @staticmethod
    def handle_schedule_followup(
        extracted_data: Dict[str, Any], 
        person_id: str, 
        person_fields: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """Handle scheduling follow-ups in Followups table"""
        
        timeline = extracted_data.get("followup_timeline", "")
        reason = extracted_data.get("followup_reason", "")
        
        if not timeline:
            return False, "❌ I couldn't determine when you'd like to schedule the follow-up. Please specify a time, like 'follow up next week' or 'follow up in 2 weeks'"
        
        # Calculate follow-up date
        followup_date = _parse_timeline_to_date(timeline)
        
        # Create follow-up record
        followup_data = {
            "Person": [person_id],
            "Reason": reason or "Scheduled follow-up",
            "Timeline": timeline,
            "Scheduled Date": followup_date.isoformat() if followup_date else None,
            "Status": "Scheduled",
            "Created At": datetime.now().isoformat(),
            "Created By": "SMS"
        }
        
        success = airtable.create_followup(followup_data)
        
        if success:
            return True, f"✅ Follow-up scheduled: {timeline}"
        else:
            return False, "❌ I couldn't schedule the follow-up in your system. This might be due to a connection issue. Please try again or contact support if the problem persists."

def _extract_person_name_from_action(action: str, person_fields: Dict[str, Any]) -> str:
    """Extract person name from reminder action or fall back to current person"""
    import re
    
    # Common patterns for person names in reminder actions
    patterns = [
        # Pattern 1: Match until time words (include 'today')
        r'(?:text|call|email|reach out to|follow up with|check in with|contact)\s+([A-Za-z\s]+?)(?:\s+(?:tomorrow|today|next|at|in|later))',
        # Pattern 2: Match until end of string (for simple cases like "text david kobrosky")
        r'(?:text|call|email|reach out to|follow up with|check in with|contact)\s+([A-Za-z\s]+)$',
        # Pattern 3: Match until punctuation
        r'(?:text|call|email|reach out to|follow up with|check in with|contact)\s+([A-Za-z\s]+?)(?:\s|,|\.)'
    ]
    
    action_lower = action.lower()
    
    # Look for person names in the action
    for pattern in patterns:
        match = re.search(pattern, action_lower)
        if match:
            extracted_name = match.group(1).strip()
            # Clean up the name (remove extra words, capitalize properly)
            name_parts = extracted_name.split()
            if len(name_parts) >= 2:  # At least first and last name
                return ' '.join([part.capitalize() for part in name_parts])
            elif len(name_parts) == 1:
                return name_parts[0].capitalize()
    
    # If no person name found in action, use current person's name, ensure non-None
    fallback_name = person_fields.get("Name")
    return fallback_name or "Unknown"

def _normalize_birthday(birthday_str: str) -> Optional[str]:
    """Normalize birthday to YYYY-MM-DD format"""
    if not birthday_str:
        return None
    
    # Handle MM/DD/YYYY format
    if "/" in birthday_str:
        try:
            parts = birthday_str.split("/")
            if len(parts) == 3:
                month, day, year = parts
                return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
        except:
            pass
    
    # Handle MM-DD-YYYY format
    if "-" in birthday_str and len(birthday_str.split("-")[0]) <= 2:
        try:
            parts = birthday_str.split("-")
            if len(parts) == 3:
                month, day, year = parts
                return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
        except:
            pass
    
    return birthday_str

def _parse_timeline_to_date(timeline: str) -> Optional[datetime]:
    """Parse natural language timeline to actual date"""
    if not timeline:
        return None
    
    timeline_lower = timeline.lower()
    now = datetime.now()
    
    # Parse various timeline expressions
    if "few months" in timeline_lower or "couple months" in timeline_lower:
        return now + timedelta(days=60)
    elif "month" in timeline_lower:
        return now + timedelta(days=30)
    elif "few weeks" in timeline_lower or "couple weeks" in timeline_lower:
        return now + timedelta(days=14)
    elif "week" in timeline_lower:
        return now + timedelta(days=7)
    elif "few days" in timeline_lower:
        return now + timedelta(days=3)
    elif "day" in timeline_lower:
        return now + timedelta(days=1)
    elif "tomorrow" in timeline_lower:
        return now + timedelta(days=1)
    elif "next week" in timeline_lower:
        return now + timedelta(days=7)
    elif "next month" in timeline_lower:
        return now + timedelta(days=30)
    
    # Try to extract numbers
    numbers = re.findall(r'\d+', timeline)
    if numbers:
        num = int(numbers[0])
        if "month" in timeline_lower:
            return now + timedelta(days=num * 30)
        elif "week" in timeline_lower:
            return now + timedelta(days=num * 7)
        elif "day" in timeline_lower:
            return now + timedelta(days=num)
    
    return None
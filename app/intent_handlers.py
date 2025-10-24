"""
Intent Handlers Module

This module contains handlers for processing different types of SMS intents.
Each handler processes a specific type of user request and updates the appropriate Airtable.
"""

from typing import Dict, Any, Tuple, Optional
from . import airtable
from . import twilio_utils
from datetime import datetime, timedelta
import re
import json

# =============================================================================
# INTENT HANDLERS CLASS
# =============================================================================

class IntentHandlers:
    """Handles processing of different SMS intents and updates appropriate Airtable tables"""
    
    # =============================================================================
    # PERSON INFO UPDATES
    # =============================================================================
    
    @staticmethod
    def handle_update_person_info(
        extracted_data: Dict[str, Any], 
        person_id: str, 
        person_fields: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """Handle updates to Core People table (Birthday, How We Met, etc.)"""
        
        field_updates = extracted_data.get("field_updates", {})
        target_person_name = extracted_data.get("target_person_name", "")
        
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
            # Always require a person name in the message - never update the texter's data
            if not target_person_name:
                return False, "❌ Please specify whose information you want to update. For example: 'update John's birthday to 3/14/1999' or 'change Sarah's company to Tech Corp'"
            
            # Find and update the person mentioned in the message
            main_person_id = None
            main_people = airtable.get_all_people()
            
            for person in main_people:
                fields = person.get("fields", {})
                person_name = fields.get("Name", "")
                if person_name.lower() == target_person_name.lower():
                    main_person_id = person["id"]
                    break
            
            if not main_person_id:
                return False, f"❌ I couldn't find a person named '{target_person_name}' in the system. Please check the spelling and try again."
            
            success = airtable.update_person(main_person_id, updates)
            if success:
                updated_fields = list(updates.keys())
                return True, f"✅ Updated {', '.join(updated_fields)} for {target_person_name}"
            else:
                return False, f"❌ I couldn't update {target_person_name}'s information in the system. This might be due to a connection issue. Please try again or contact support if the problem persists."
        
        return False, "❌ I couldn't determine what information you'd like me to update. Please be specific, like 'update John's birthday to 03/14/1999' or 'change Sarah's company to Tech Corp'"
    
    # =============================================================================
    # TAG MANAGEMENT
    # =============================================================================
    
    @staticmethod
    def handle_manage_tags(
        extracted_data: Dict[str, Any], 
        person_id: str, 
        person_fields: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """Handle tag operations - updates People table Tags field"""
        
        tags_to_add = extracted_data.get("tags_to_add", [])
        tags_to_remove = extracted_data.get("tags_to_remove", [])
        target_person_name = extracted_data.get("target_person_name", "")
        
        if not tags_to_add and not tags_to_remove:
            return False, "❌ I couldn't determine which tags you'd like to add or remove. Please be specific, like 'tag John with mentor' or 'remove the developer tag from Sarah'"
        
        # Always require a target person name - never update the texter's data
        if not target_person_name:
            return False, "❌ Please specify whose tags you want to update. For example: 'tag John with mentor' or 'remove the developer tag from Sarah'"
        
        # Find the target person in the main people table
        target_person = airtable.find_person_by_name(target_person_name)
        if not target_person:
            return False, f"❌ I couldn't find '{target_person_name}' in your contacts. Please check the spelling or add them first."
        
        target_person_id = target_person["id"]
        target_person_fields = target_person.get("fields", {})
        
        # Get current tags from target person's record
        current_tags = target_person_fields.get("Tags", [])
        
        # Add new tags
        if tags_to_add:
            current_tags.extend(tags_to_add)
        
        # Remove specified tags
        if tags_to_remove:
            current_tags = [tag for tag in current_tags if tag not in tags_to_remove]
        
        # Remove duplicates
        current_tags = list(set(current_tags))
        
        success = airtable.update_person(target_person_id, {"Tags": current_tags})
        
        if success:
            messages = []
            if tags_to_add:
                messages.append(f"Added: {', '.join(tags_to_add)}")
            if tags_to_remove:
                messages.append(f"Removed: {', '.join(tags_to_remove)}")
            return True, f"✅ Tags updated for {target_person_name} - {', '.join(messages)}"
        else:
            return False, f"❌ I couldn't update {target_person_name}'s tags in the system. This might be due to a connection issue. Please try again or contact support if the problem persists."
    
    # =============================================================================
    # REMINDER MANAGEMENT
    # =============================================================================
    
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
        
        due_date_str = due_date.isoformat() if due_date else None
        
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
    
    # =============================================================================
    # NOTE MANAGEMENT
    # =============================================================================
    
    @staticmethod
    def handle_create_note(
        extracted_data: Dict[str, Any], 
        person_id: str, 
        person_fields: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """Handle creating notes in Notes table"""
        
        note_content = extracted_data.get("note_content", "")
        target_person_name = extracted_data.get("target_person_name", "")
        
        if not note_content:
            return False, "❌ I couldn't determine what note you'd like me to add. Please be more specific, like 'note: John mentioned he's interested in the PM role'"
        
        # If there's a target person, find them first
        target_person_id = person_id  # Default to current person
        if target_person_name:
            # Find the target person in the main people table
            target_person = airtable.find_person_by_name(target_person_name)
            if target_person:
                target_person_id = target_person["id"]
            else:
                return False, f"❌ I couldn't find '{target_person_name}' in your contacts. Please check the spelling or add them first."
        
        # Create note record
        note_data = {
            "Person": [target_person_id],
            "Content": note_content,
            "Type": "SMS Note",
            "Created At": datetime.now().isoformat(),
            "Created By": "SMS"
        }
        
        success = airtable.create_note(note_data)
        
        if success:
            target_text = f" for {target_person_name}" if target_person_name else ""
            return True, f"✅ Note added{target_text}: {note_content[:50]}{'...' if len(note_content) > 50 else ''}"
        else:
            return False, "❌ I couldn't save the note to your system. This might be due to a connection issue. Please try again or contact support if the problem persists."
    
    # =============================================================================
    # FOLLOW-UP MANAGEMENT
    # =============================================================================
    
    @staticmethod
    def handle_schedule_followup(
        extracted_data: Dict[str, Any], 
        person_id: str, 
        person_fields: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """Handle scheduling follow-ups in Followups table"""
        
        timeline = extracted_data.get("followup_timeline", "")
        reason = extracted_data.get("followup_reason", "")
        target_person_name = extracted_data.get("target_person_name", "")
        
        if not timeline:
            return False, "❌ I couldn't determine when you'd like to schedule the follow-up. Please specify a time, like 'follow up with John next week' or 'follow up with Sarah in 2 weeks'"
        
        # Always require a target person name - never schedule follow-up for the texter
        if not target_person_name:
            return False, "❌ Please specify who you'd like to follow up with. For example: 'follow up with John next week' or 'follow up with Sarah in 2 weeks'"
        
        # Find the target person in the main people table
        target_person = airtable.find_person_by_name(target_person_name)
        if not target_person:
            return False, f"❌ I couldn't find '{target_person_name}' in your contacts. Please check the spelling or add them first."
        
        target_person_id = target_person["id"]
        
        # Calculate follow-up date
        followup_date = _parse_timeline_to_date(timeline)
        
        # Create follow-up record
        followup_data = {
            "Person": [target_person_id],
            "Reason": reason or f"Follow up with {target_person_name}",
            "Timeline": timeline,
            "Scheduled Date": followup_date.isoformat() if followup_date else None,
            "Status": "Scheduled",
            "Created At": datetime.now().isoformat(),
            "Created By": "SMS"
        }
        
        success = airtable.create_followup(followup_data)
        
        if success:
            return True, f"✅ Follow-up scheduled with {target_person_name}: {timeline}"
        else:
            return False, f"❌ I couldn't schedule the follow-up with {target_person_name} in your system. This might be due to a connection issue. Please try again or contact support if the problem persists."
    
    # =============================================================================
    # FRIEND MANAGEMENT
    # =============================================================================
    
    @staticmethod
    def handle_new_friend(
        extracted_data: Dict[str, Any], 
        person_id: str, 
        person_fields: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """Handle creating new friends in Core People table"""
        
        friend_name = extracted_data.get("friend_name", "")
        
        if not friend_name:
            return False, "❌ I couldn't determine the name of the friend you'd like to add. Please specify a name, like 'new friend John Smith'"
        
        # Check if person already exists
        from .admin_sms import find_person_by_name
        existing_person = find_person_by_name(friend_name)
        if existing_person:
            return False, f"❌ Person '{friend_name}' already exists in Airtable"
        
        # Create new person with just the name
        person_id = airtable.create_person({"Name": friend_name})
        if person_id:
            # Add small delay to ensure Airtable has processed the write
            import time
            time.sleep(0.5)
            return True, f"✅ Added new friend '{friend_name}' to Airtable"
        else:
            return False, f"❌ Failed to create new friend '{friend_name}'"

    # =============================================================================
    # DATA QUERYING
    # =============================================================================
    
    @staticmethod
    def handle_query_data(
        extracted_data: Dict[str, Any], 
        person_id: str, 
        person_fields: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """Handle queries about data in Airtables"""
        
        query_type = extracted_data.get("query_type", "people")
        query_terms = extracted_data.get("query_terms", [])
        
        # Handle case where query_terms might be a string instead of array
        if isinstance(query_terms, str):
            query_terms = [query_terms]
        
        if not query_terms:
            return False, "❌ I couldn't determine what you're looking for. Please be specific, like 'Is David Kobrosky in here?' or 'Do I have any reminders about Sarah?'"
        
        try:
            if query_type == "people":
                return IntentHandlers._query_people(query_terms)
            elif query_type == "reminders":
                return IntentHandlers._query_reminders(query_terms)
            elif query_type == "notes":
                return IntentHandlers._query_notes(query_terms)
            elif query_type == "checkins":
                return IntentHandlers._query_checkins(query_terms)
            else:
                return False, f"❌ I don't know how to search for {query_type}. I can search people, reminders, notes, or checkins."
        except Exception as e:
            return False, f"❌ Error searching data: {str(e)}"
    
    @staticmethod
    def _query_people(query_terms: list) -> Tuple[bool, str]:
        """Query people in the main people table"""
        try:
            all_people = airtable.get_all_people()
            matches = []
            
            for person in all_people:
                fields = person.get("fields", {})
                person_name = fields.get("Name", "")
                
                # Check if any query term matches the person's name (case-insensitive)
                for term in query_terms:
                    if term.lower() in person_name.lower():
                        matches.append({
                            "name": person_name,
                            "email": fields.get("Email", "No email"),
                            "phone": fields.get("Phone", "No phone"),
                            "company": fields.get("Company", "No company"),
                            "role": fields.get("Role", "No role"),
                            "birthday": fields.get("Birthday", "No birthday"),
                            "tags": fields.get("Tags", [])
                        })
                        break
            
            if not matches:
                return True, f"❌ No people found matching: {', '.join(query_terms)}"
            
            if len(matches) == 1:
                person = matches[0]
                response = f"✅ Found {person['name']}:\n"
                response += f"📧 Email: {person['email']}\n"
                response += f"📞 Phone: {person['phone']}\n"
                response += f"🏢 Company: {person['company']}\n"
                response += f"💼 Role: {person['role']}\n"
                response += f"🎂 Birthday: {person['birthday']}\n"
                if person['tags']:
                    response += f"🏷️ Tags: {', '.join(person['tags'])}"
                return True, response
            else:
                response = f"✅ Found {len(matches)} people matching: {', '.join(query_terms)}\n\n"
                for i, person in enumerate(matches, 1):
                    response += f"{i}. {person['name']} ({person['email']})\n"
                return True, response
                
        except Exception as e:
            return False, f"❌ Error searching people: {str(e)}"
    
    @staticmethod
    def _query_reminders(query_terms: list) -> Tuple[bool, str]:
        """Query reminders table"""
        try:
            # Get all reminders
            reminders = airtable.get_all_reminders()
            matches = []
            
            for reminder in reminders:
                fields = reminder.get("fields", {})
                action = fields.get("Action", "")
                person_name = fields.get("Person Name", "")
                
                # Check if any query term matches the action or person name
                for term in query_terms:
                    if (term.lower() in action.lower() or 
                        term.lower() in person_name.lower()):
                        matches.append({
                            "action": action,
                            "person": person_name,
                            "timeline": fields.get("Timeline", "No timeline"),
                            "priority": fields.get("Priority", "No priority"),
                            "status": fields.get("Status", "No status"),
                            "created": fields.get("Created", "Unknown date")
                        })
                        break
            
            if not matches:
                return True, f"❌ No reminders found matching: {', '.join(query_terms)}"
            
            response = f"✅ Found {len(matches)} reminder(s) matching: {', '.join(query_terms)}\n\n"
            for i, reminder in enumerate(matches, 1):
                response += f"{i}. {reminder['action']}\n"
                response += f"   👤 Person: {reminder['person']}\n"
                response += f"   ⏰ Timeline: {reminder['timeline']}\n"
                response += f"   🔥 Priority: {reminder['priority']}\n"
                response += f"   📊 Status: {reminder['status']}\n\n"
            
            return True, response
            
        except Exception as e:
            return False, f"❌ Error searching reminders: {str(e)}"
    
    @staticmethod
    def _query_notes(query_terms: list) -> Tuple[bool, str]:
        """Query notes (stored in How We Met field of people)"""
        try:
            all_people = airtable.get_all_people()
            matches = []
            
            for person in all_people:
                fields = person.get("fields", {})
                person_name = fields.get("Name", "")
                how_we_met = fields.get("How We Met", "")
                
                # Check if any query term matches the person's name or notes
                for term in query_terms:
                    if (term.lower() in person_name.lower() or 
                        term.lower() in how_we_met.lower()):
                        matches.append({
                            "name": person_name,
                            "notes": how_we_met
                        })
                        break
            
            if not matches:
                return True, f"❌ No notes found matching: {', '.join(query_terms)}"
            
            response = f"✅ Found {len(matches)} person(s) with notes matching: {', '.join(query_terms)}\n\n"
            for i, match in enumerate(matches, 1):
                response += f"{i}. {match['name']}:\n"
                response += f"   📝 {match['notes']}\n\n"
            
            return True, response
            
        except Exception as e:
            return False, f"❌ Error searching notes: {str(e)}"
    
    @staticmethod
    def _query_checkins(query_terms: list) -> Tuple[bool, str]:
        """Query check-ins table"""
        try:
            # Get all check-ins
            checkins = airtable.get_all_checkins()
            matches = []
            
            for checkin in checkins:
                fields = checkin.get("fields", {})
                person_name = fields.get("Person Name", "")
                month = fields.get("Month", "")
                status = fields.get("Status", "")
                
                # Check if any query term matches the person's name
                for term in query_terms:
                    if term.lower() in person_name.lower():
                        matches.append({
                            "person": person_name,
                            "month": month,
                            "status": status,
                            "created": fields.get("Created", "Unknown date")
                        })
                        break
            
            if not matches:
                return True, f"❌ No check-ins found matching: {', '.join(query_terms)}"
            
            response = f"✅ Found {len(matches)} check-in(s) matching: {', '.join(query_terms)}\n\n"
            for i, checkin in enumerate(matches, 1):
                response += f"{i}. {checkin['person']} - {checkin['month']}\n"
                response += f"   📊 Status: {checkin['status']}\n"
                response += f"   📅 Created: {checkin['created']}\n\n"
            
            return True, response
            
        except Exception as e:
            return False, f"❌ Error searching check-ins: {str(e)}"

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

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
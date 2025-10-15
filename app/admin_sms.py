"""
Admin SMS Module

This module handles admin-specific SMS commands and provides utilities
for parsing and executing administrative functions. It includes MCP parser
integration for complex command parsing and fallback regex-based parsing.
"""

import re
import asyncio
from typing import Dict, Any, Optional, Tuple
from . import airtable

# =============================================================================
# MCP PARSER INTEGRATION
# =============================================================================

# Import MCP client for complex parsing
try:
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(__file__)))
    from mcp_parser.mcp_sync_client import test_mcp_sync
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    print("MCP client not available, falling back to regex-only parsing")

# =============================================================================
# CONFIGURATION
# =============================================================================

# Admin phone numbers (add more as needed)
ADMIN_NUMBERS = {
    "+19784910236",  # David's number
    "9784910236"     # Also accept without +1
}

# =============================================================================
# ADMIN UTILITIES
# =============================================================================

def is_admin_number(phone: str) -> bool:
    """Check if a phone number is an admin number"""
    # Normalize phone number
    normalized = phone.replace("+1", "") if phone.startswith("+1") else phone
    return normalized in ADMIN_NUMBERS or phone in ADMIN_NUMBERS

# =============================================================================
# COMMAND PARSING
# =============================================================================

def parse_admin_command(message: str) -> Optional[Dict[str, Any]]:
    """
    Parse admin SMS commands using hybrid approach:
    1. Try regex patterns first (fast, simple commands)
    2. Fall back to MCP for complex natural language
    
    Supported formats:
    - new friend [Name]
    - add birthday [Name] [YYYY-MM-DD]
    - add email [Name] [Email]
    - add phone [Name] [Phone]
    - add linkedin [Name] [LinkedIn URL]
    - change role [Name] [New Role]
    - change company [Name] [New Company]
    - Natural language: "can you add linkedin for bobby housel - here's the url..."
    """
    message = message.strip()
    
    # First try regex patterns (fast, simple commands)
    regex_result = _parse_with_regex(message)
    if regex_result:
        return regex_result
    
    # If regex fails and MCP is available, try MCP for complex parsing
    if MCP_AVAILABLE:
        try:
            # Use synchronous MCP client that works within async contexts
            mcp_result = test_mcp_sync(message)
            
            if mcp_result and mcp_result.get("command") and mcp_result.get("confidence", 0) > 0.5:
                # Convert MCP result to our expected format
                return _convert_mcp_result(mcp_result)
        except Exception as e:
            print(f"Error with MCP parsing: {e}")
            pass
    
    return None

def _parse_with_regex(message: str) -> Optional[Dict[str, Any]]:
    """Parse using regex patterns (original logic)"""
    
    # Pattern for adding birthday - support both YYYY-MM-DD and MM/DD/YYYY formats
    birthday_pattern_iso = r'^add\s+birthday\s+(.+?)\s+(\d{4}-\d{2}-\d{2})$'
    birthday_pattern_us = r'^add\s+birthday\s+(.+?)\s+(\d{1,2}/\d{1,2}/\d{4})$'
    
    birthday_match_iso = re.match(birthday_pattern_iso, message, re.IGNORECASE)
    birthday_match_us = re.match(birthday_pattern_us, message, re.IGNORECASE)
    
    if birthday_match_iso:
        name = birthday_match_iso.group(1).strip()
        birthday = birthday_match_iso.group(2)
        return {
            "command": "add_birthday",
            "name": name,
            "birthday": birthday
        }
    elif birthday_match_us:
        name = birthday_match_us.group(1).strip()
        birthday_str = birthday_match_us.group(2)
        # Convert MM/DD/YYYY to YYYY-MM-DD
        try:
            from datetime import datetime
            birthday_date = datetime.strptime(birthday_str, "%m/%d/%Y")
            birthday = birthday_date.strftime("%Y-%m-%d")
        except ValueError:
            return None
        return {
            "command": "add_birthday",
            "name": name,
            "birthday": birthday
        }
    
    # Pattern for changing role
    role_pattern = r'^change\s+role\s+(.+?)\s+(.+)$'
    role_match = re.match(role_pattern, message, re.IGNORECASE)
    
    if role_match:
        name = role_match.group(1).strip()
        new_role = role_match.group(2).strip()
        return {
            "command": "change_role",
            "name": name,
            "new_role": new_role
        }
    
    # Pattern for changing company
    company_pattern = r'^change\s+company\s+(.+?)\s+(.+)$'
    company_match = re.match(company_pattern, message, re.IGNORECASE)
    
    if company_match:
        name = company_match.group(1).strip()
        new_company = company_match.group(2).strip()
        return {
            "command": "change_company",
            "name": name,
            "new_company": new_company
        }
    
    # Pattern for adding new friend
    new_friend_pattern = r'^new\s+friend\s+(.+)$'
    new_friend_match = re.match(new_friend_pattern, message, re.IGNORECASE)
    
    if new_friend_match:
        name = new_friend_match.group(1).strip()
        return {
            "command": "new_friend",
            "name": name
        }
    
    # Pattern for adding email - handle both quoted and unquoted emails
    email_pattern = r'^add\s+email\s+(.+?)\s+["\']?([^\s"\'<>]+@[^\s"\'<>]+\.[^\s"\'<>]+)["\']?$'
    email_match = re.match(email_pattern, message, re.IGNORECASE)
    
    if email_match:
        name = email_match.group(1).strip()
        email = email_match.group(2).strip()
        return {
            "command": "add_email",
            "name": name,
            "email": email
        }
    
    # Pattern for adding phone - handle both quoted and unquoted phone numbers
    phone_pattern = r'^add\s+phone\s+(.+?)\s+["\']?(\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}|[0-9]{10,11}|\+?[0-9]{10,15})["\']?$'
    phone_match = re.match(phone_pattern, message, re.IGNORECASE)
    
    if phone_match:
        name = phone_match.group(1).strip()
        phone = phone_match.group(2).strip()
        return {
            "command": "add_phone",
            "name": name,
            "phone": phone
        }
    
    # Pattern for adding LinkedIn - handle both quoted and unquoted URLs
    linkedin_pattern = r'^add\s+linkedin\s+(.+?)\s+["\']?(https?://[^\s"\'<>]+|linkedin\.com/[^\s"\'<>]+)["\']?$'
    linkedin_match = re.match(linkedin_pattern, message, re.IGNORECASE)
    
    if linkedin_match:
        name = linkedin_match.group(1).strip()
        linkedin = linkedin_match.group(2).strip()
        return {
            "command": "add_linkedin",
            "name": name,
            "linkedin": linkedin
        }
    
    return None

def _convert_mcp_result(mcp_result: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Convert MCP result to our expected format"""
    if not mcp_result or not mcp_result.get("command"):
        return None
    
    command = mcp_result["command"]
    name = mcp_result.get("name")
    extracted_data = mcp_result.get("extracted_data", {})
    
    # Convert MCP command names to our expected format
    if command == "add_linkedin":
        return {
            "command": "add_linkedin",
            "name": name,
            "linkedin": mcp_result.get("linkedin") or extracted_data.get("linkedin")
        }
    elif command == "add_email":
        return {
            "command": "add_email", 
            "name": name,
            "email": mcp_result.get("email") or extracted_data.get("email")
        }
    elif command == "add_phone":
        return {
            "command": "add_phone",
            "name": name,
            "phone": mcp_result.get("phone") or extracted_data.get("phone")
        }
    elif command == "add_birthday":
        return {
            "command": "add_birthday",
            "name": name,
            "birthday": mcp_result.get("birthday") or extracted_data.get("birthday")
        }
    elif command == "new_friend":
        return {
            "command": "new_friend",
            "name": name
        }
    elif command == "update_company":
        return {
            "command": "change_company",
            "name": name,
            "new_company": mcp_result.get("company") or extracted_data.get("company")
        }
    elif command == "create_reminder":
        return {
            "command": "create_reminder",
            "name": name,
            "reminder_action": mcp_result.get("reminder_action", ""),
            "reminder_timeline": mcp_result.get("reminder_timeline", "unspecified"),
            "reminder_priority": mcp_result.get("reminder_priority", "medium")
        }
    
    return None

# =============================================================================
# PERSON LOOKUP
# =============================================================================

def find_person_by_name(name: str) -> Optional[Dict[str, Any]]:
    """Find a person in Airtable by name"""
    try:
        # Get all people from the Checkins table
        people = airtable.get_all_people()
        
        # Search for person by name (case-insensitive)
        name_lower = name.lower()
        for person in people:
            person_name = person.get('fields', {}).get('Name', '')
            if name_lower in person_name.lower():
                return person
        
        return None
    except Exception as e:
        print(f"Error finding person by name: {e}")
        return None

# =============================================================================
# COMMAND EXECUTION
# =============================================================================

def execute_admin_command(command_data: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Execute an admin command and return (success, message)
    """
    try:
        command = command_data.get("command")
        name = command_data.get("name")
        
        # Handle new friend command (create new person)
        if command == "new_friend":
            # Check if person already exists
            existing_person = find_person_by_name(name)
            if existing_person:
                return False, f"❌ Person '{name}' already exists in Airtable"
            
            # Create new person with just the name
            person_id = airtable.create_person({"Name": name})
            if person_id:
                # Add small delay to ensure Airtable has processed the write
                import time
                time.sleep(0.5)
                return True, f"✅ Added new friend '{name}' to Airtable"
            else:
                return False, f"❌ Failed to create new friend '{name}'"
        
        # For other commands, find the person first
        person = find_person_by_name(name)
        if not person:
            return False, f"❌ Person '{name}' not found in Airtable"
        
        person_id = person["id"]
        person_fields = person.get("fields", {})
        
        if command == "add_birthday":
            birthday = command_data.get("birthday")
            
            # Update the person record
            success = airtable.update_person(person_id, {"Birthday": birthday})
            
            if success:
                return True, f"✅ Added birthday {birthday} for {name}"
            else:
                return False, f"❌ Failed to update birthday for {name}"
        
        elif command == "change_role":
            new_role = command_data.get("new_role")
            
            # Update the person record
            success = airtable.update_person(person_id, {"Role": new_role})
            
            if success:
                return True, f"✅ Changed {name}'s role to {new_role}"
            else:
                return False, f"❌ Failed to update role for {name}"
        
        elif command == "change_company":
            new_company = command_data.get("new_company")
            
            # Update the person record
            success = airtable.update_person(person_id, {"Company": new_company})
            
            if success:
                return True, f"✅ Changed {name}'s company to {new_company}"
            else:
                return False, f"❌ Failed to update company for {name}"
        
        elif command == "add_email":
            email = command_data.get("email")
            
            # Update the person record
            success = airtable.update_person(person_id, {"Email": email})
            
            if success:
                return True, f"✅ Added email {email} for {name}"
            else:
                return False, f"❌ Failed to update email for {name}"
        
        elif command == "add_phone":
            phone = command_data.get("phone")
            
            # Update the person record
            success = airtable.update_person(person_id, {"Phone": phone})
            
            if success:
                return True, f"✅ Added phone {phone} for {name}"
            else:
                return False, f"❌ Failed to update phone for {name}"
        
        elif command == "add_linkedin":
            linkedin = command_data.get("linkedin")
            
            # Update the person record
            success = airtable.update_person(person_id, {"LinkedIn": linkedin})
            
            if success:
                return True, f"✅ Added LinkedIn {linkedin} for {name}"
            else:
                return False, f"❌ Failed to update LinkedIn for {name}"
        
        elif command == "create_reminder":
            reminder_action = command_data.get("reminder_action", "")
            reminder_timeline = command_data.get("reminder_timeline", "unspecified")
            reminder_priority = command_data.get("reminder_priority", "medium")
            
            # Create reminder using the new function
            success = airtable.create_reminder_for_person(
                person_name=name,
                reminder_text=reminder_action,
                due_date=None  # Will be calculated from timeline
            )
            
            if success:
                timeline_text = f" (due: {reminder_timeline})" if reminder_timeline != "unspecified" else ""
                return True, f"✅ Reminder created for {name}: {reminder_action}{timeline_text}"
            else:
                return False, f"❌ Failed to create reminder for {name}"
        
        else:
            return False, f"❌ Unknown command: {command}"
            
    except Exception as e:
        print(f"Error executing admin command: {e}")
        return False, f"❌ Error executing command: {str(e)}"

# =============================================================================
# HELP SYSTEM
# =============================================================================

def get_admin_help() -> str:
    """Get help text for admin commands"""
    return """📋 Admin Commands:
• new friend [Name]
• add birthday [Name] [Date]
• add email [Name] [Email]
• add phone [Name] [Phone]
• add linkedin [Name] [URL]
• change role [Name] [Role]
• change company [Name] [Company]
• help/controls - Show commands""" 
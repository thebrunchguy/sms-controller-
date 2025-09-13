import re
from typing import Dict, Any, Optional, Tuple
from . import airtable

# Admin phone numbers (add more as needed)
ADMIN_NUMBERS = {
    "+19784910236",  # David's number
    "9784910236"     # Also accept without +1
}

def is_admin_number(phone: str) -> bool:
    """Check if a phone number is an admin number"""
    # Normalize phone number
    normalized = phone.replace("+1", "") if phone.startswith("+1") else phone
    return normalized in ADMIN_NUMBERS or phone in ADMIN_NUMBERS

def parse_admin_command(message: str) -> Optional[Dict[str, Any]]:
    """
    Parse admin SMS commands
    
    Supported formats:
    - new friend [Name]
    - add birthday [Name] [YYYY-MM-DD]
    - add email [Name] [Email]
    - add phone [Name] [Phone]
    - add linkedin [Name] [LinkedIn URL]
    - change role [Name] [New Role]
    - change company [Name] [New Company]
    """
    message = message.strip()
    
    # Pattern for adding birthday
    birthday_pattern = r'^add\s+birthday\s+(.+?)\s+(\d{4}-\d{2}-\d{2})$'
    birthday_match = re.match(birthday_pattern, message, re.IGNORECASE)
    
    if birthday_match:
        name = birthday_match.group(1).strip()
        birthday = birthday_match.group(2)
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
    
    # Pattern for adding email
    email_pattern = r'^add\s+email\s+(.+?)\s+([^\s]+@[^\s]+\.[^\s]+)$'
    email_match = re.match(email_pattern, message, re.IGNORECASE)
    
    if email_match:
        name = email_match.group(1).strip()
        email = email_match.group(2).strip()
        return {
            "command": "add_email",
            "name": name,
            "email": email
        }
    
    # Pattern for adding phone
    phone_pattern = r'^add\s+phone\s+(.+?)\s+(\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}|[0-9]{10,11}|\+?[0-9]{10,15})$'
    phone_match = re.match(phone_pattern, message, re.IGNORECASE)
    
    if phone_match:
        name = phone_match.group(1).strip()
        phone = phone_match.group(2).strip()
        return {
            "command": "add_phone",
            "name": name,
            "phone": phone
        }
    
    # Pattern for adding LinkedIn
    linkedin_pattern = r'^add\s+linkedin\s+(.+?)\s+(https?://[^\s]+|linkedin\.com/[^\s]+)$'
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
        
        else:
            return False, f"❌ Unknown command: {command}"
            
    except Exception as e:
        print(f"Error executing admin command: {e}")
        return False, f"❌ Error executing command: {str(e)}"

def get_admin_help() -> str:
    """Get help text for admin commands"""
    return """📋 Admin Commands:

• new friend [Name]
  Example: new friend Sarah Johnson

• add birthday [Name] [YYYY-MM-DD]
  Example: add birthday John Doe 1990-05-15

• add email [Name] [Email]
  Example: add email John Doe john@example.com

• add phone [Name] [Phone]
  Example: add phone John Doe +1234567890

• add linkedin [Name] [LinkedIn URL]
  Example: add linkedin John Doe https://linkedin.com/in/johndoe

• change role [Name] [New Role]
  Example: change role John Doe Senior Developer

• change company [Name] [New Company]
  Example: change company John Doe Google

• help - Show this help message
• controls - Show this help message (same as help)

Note: Use exact names as they appear in Airtable""" 
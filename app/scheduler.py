import os
from datetime import datetime, date, timedelta
from typing import List, Dict, Any
from . import airtable

def get_people_due_for_checkin() -> List[Dict[str, Any]]:
    """
    Get people who are due for monthly check-in based on frequency and last confirmed date
    
    Returns:
        List of person records that need check-ins
    """
    try:
        # Get all people with monthly frequency who haven't opted out
        people = airtable.get_people_due_for_checkin()
        
        if not people:
            return []
        
        # Filter by actual due date logic
        today = date.today()
        due_people = []
        
        for person in people:
            if is_due_for_checkin(person, today):
                due_people.append(person)
        
        return due_people
        
    except Exception as e:
        print(f"Error getting people due for checkin: {e}")
        return []

def is_due_for_checkin(person: Dict[str, Any], current_date: date) -> bool:
    """
    Determine if a person is due for a check-in
    
    Args:
        person: Person record from Airtable
        current_date: Current date to check against
        
    Returns:
        True if person is due for check-in, False otherwise
    """
    try:
        fields = person.get("fields", {})
        
        # Check if person has opted out
        if fields.get("Opt-out"):
            return False
        
        # Check if person has given consent
        if not fields.get("Consent"):
            return False
        
        # Get check-in frequency
        frequency = fields.get("Check-in Frequency", "Monthly")
        
        if frequency not in ["Monthly", "Quarterly"]:
            return False
        
        # Get last confirmed date
        last_confirmed_str = fields.get("Last Confirmed")
        
        if not last_confirmed_str:
            # Never confirmed, so they're due
            return True
        
        try:
            # Parse the last confirmed date
            if isinstance(last_confirmed_str, str):
                last_confirmed = datetime.strptime(last_confirmed_str, "%Y-%m-%d").date()
            else:
                # Assume it's already a date object
                last_confirmed = last_confirmed_str
            
            # Calculate due date based on frequency
            if frequency == "Monthly":
                due_date = last_confirmed + timedelta(days=30)
            else:  # Quarterly
                due_date = last_confirmed + timedelta(days=90)
            
            # Check if current date is past due date
            return current_date >= due_date
            
        except (ValueError, TypeError) as e:
            print(f"Error parsing last confirmed date for person {person.get('id')}: {e}")
            # If we can't parse the date, assume they're due
            return True
            
    except Exception as e:
        print(f"Error checking if person is due for checkin: {e}")
        return False

def get_monthly_checkin_stats() -> Dict[str, Any]:
    """
    Get statistics about monthly check-ins
    
    Returns:
        Dictionary with check-in statistics
    """
    try:
        current_month = datetime.now().strftime("%Y-%m")
        
        # This would require additional Airtable functions to get comprehensive stats
        # For now, return basic info
        stats = {
            "current_month": current_month,
            "total_people": 0,
            "due_this_month": 0,
            "sent_this_month": 0,
            "completed_this_month": 0,
            "opted_out": 0
        }
        
        # Get people due for check-in
        due_people = get_people_due_for_checkin()
        stats["due_this_month"] = len(due_people)
        
        return stats
        
    except Exception as e:
        print(f"Error getting monthly checkin stats: {e}")
        return {}

def should_skip_person(person: Dict[str, Any]) -> tuple[bool, str]:
    """
    Determine if a person should be skipped for check-in and why
    
    Args:
        person: Person record from Airtable
        
    Returns:
        Tuple of (should_skip, reason)
    """
    fields = person.get("fields", {})
    
    # Check opt-out
    if fields.get("Opt-out"):
        return True, "Person has opted out"
    
    # Check consent
    if not fields.get("Consent"):
        return True, "Person has not given consent"
    
    # Check if they have a phone number
    if not fields.get("Phone"):
        return True, "No phone number available"
    
    # Check frequency
    frequency = fields.get("Check-in Frequency")
    if frequency not in ["Monthly", "Quarterly"]:
        return True, f"Invalid check-in frequency: {frequency}"
    
    # Check if they're actually due
    if not is_due_for_checkin(person, date.today()):
        return True, "Not due for check-in yet"
    
    return False, ""

def get_next_checkin_date(person: Dict[str, Any]) -> date:
    """
    Calculate the next check-in date for a person
    
    Args:
        person: Person record from Airtable
        
    Returns:
        Next check-in date
    """
    try:
        fields = person.get("fields", {})
        last_confirmed_str = fields.get("Last Confirmed")
        frequency = fields.get("Check-in Frequency", "Monthly")
        
        if not last_confirmed_str:
            # If never confirmed, next check-in is today
            return date.today()
        
        # Parse last confirmed date
        if isinstance(last_confirmed_str, str):
            last_confirmed = datetime.strptime(last_confirmed_str, "%Y-%m-%d").date()
        else:
            last_confirmed = last_confirmed_str
        
        # Calculate next check-in date
        if frequency == "Monthly":
            next_date = last_confirmed + timedelta(days=30)
        else:  # Quarterly
            next_date = last_confirmed + timedelta(days=90)
        
        return next_date
        
    except Exception as e:
        print(f"Error calculating next checkin date: {e}")
        # Fallback: return today + 30 days
        return date.today() + timedelta(days=30)

def get_overdue_people() -> List[Dict[str, Any]]:
    """
    Get people who are overdue for check-in (past their due date)
    
    Returns:
        List of overdue person records
    """
    try:
        all_people = airtable.get_people_due_for_checkin()
        overdue_people = []
        today = date.today()
        
        for person in all_people:
            fields = person.get("fields", {})
            last_confirmed_str = fields.get("Last Confirmed")
            
            if not last_confirmed_str:
                continue
            
            try:
                if isinstance(last_confirmed_str, str):
                    last_confirmed = datetime.strptime(last_confirmed_str, "%Y-%m-%d").date()
                else:
                    last_confirmed = last_confirmed_str
                
                frequency = fields.get("Check-in Frequency", "Monthly")
                due_date = last_confirmed + timedelta(days=30 if frequency == "Monthly" else 90)
                
                if today > due_date:
                    overdue_people.append(person)
                    
            except (ValueError, TypeError):
                continue
        
        return overdue_people
        
    except Exception as e:
        print(f"Error getting overdue people: {e}")
        return []

import re
from typing import Dict, Any, Optional

def parse_sms_fallback(inbound_text: str) -> Dict[str, Any]:
    """
    Fallback SMS parser using regex patterns when LLM is disabled
    
    Args:
        inbound_text: Raw SMS text from user
        
    Returns:
        Dictionary with parsed intent and extracted fields
    """
    text = inbound_text.strip().lower()
    
    # Check for opt-out
    if re.search(r'\b(stop|unsubscribe|opt.?out|quit)\b', text):
        return {
            "intent": "opt_out",
            "confidence": 0.9,
            "confirmation_text": "You have been unsubscribed from monthly check-ins."
        }
    
    # Check for no change responses
    no_change_patterns = [
        r'\b(no\s+change|no\s+changes?)\b',
        r'\b(nothing\s+changed?|same|all\s+good|correct|accurate)\b',
        r'\b(no\s+updates?|no\s+news)\b'
    ]
    
    for pattern in no_change_patterns:
        if re.search(pattern, text):
            return {
                "intent": "no_change",
                "confidence": 0.8,
                "confirmation_text": "Thanks for confirming! No changes needed."
            }
    
    # Check for confirmation responses
    yes_patterns = [
        r'\b(yes|yeah|yep|correct|right|that\s+right|confirm)\b',
        r'\b(apply|go\s+ahead|do\s+it)\b'
    ]
    
    for pattern in yes_patterns:
        if re.search(pattern, text):
            return {
                "intent": "confirm",
                "confidence": 0.8,
                "confirmation_text": "Great! I'll apply those changes."
            }
    
    # Extract company changes
    company_patterns = [
        r'(?:left|quit|resigned\s+from|no\s+longer\s+at)\s+([A-Z][A-Za-z\s&]+?)(?:\s|$|,|\.)',
        r'(?:now\s+at|working\s+at|joined|started\s+at)\s+([A-Z][A-Za-z\s&]+?)(?:\s|$|,|\.)',
        r'(?:moved\s+to|switched\s+to)\s+([A-Z][A-Za-z\s&]+?)(?:\s|$|,|\.)'
    ]
    
    company = None
    for pattern in company_patterns:
        match = re.search(pattern, text)
        if match:
            company = match.group(1).strip()
            break
    
    # Extract role changes
    role_patterns = [
        r'(?:as\s+a?\s+)([A-Z][A-Za-z\s]+?)(?:\s|$|,|\.)',
        r'(?:role\s+is\s+)([A-Z][A-Za-z\s]+?)(?:\s|$|,|\.)',
        r'(?:position\s+is\s+)([A-Z][A-Za-z\s]+?)(?:\s|$|,|\.)'
    ]
    
    role = None
    for pattern in role_patterns:
        match = re.search(pattern, text)
        if match:
            role = match.group(1).strip()
            break
    
    # Extract city changes
    city_patterns = [
        r'(?:moved\s+to|relocated\s+to|now\s+in)\s+([A-Z][A-Za-z\s]+?)(?:\s|$|,|\.)',
        r'(?:based\s+in|located\s+in)\s+([A-Z][A-Za-z\s]+?)(?:\s|$|,|\.)'
    ]
    
    city = None
    for pattern in city_patterns:
        match = re.search(pattern, text)
        if match:
            city = match.group(1).strip()
            break
    
    # Extract tag additions
    tag_add_patterns = [
        r'(?:also\s+)([A-Z][A-Za-z\s]+?)(?:\s|$|,|\.)',
        r'(?:additionally\s+)([A-Z][A-Za-z\s]+?)(?:\s|$|,|\.)',
        r'(?:plus\s+)([A-Z][A-Za-z\s]+?)(?:\s|$|,|\.)'
    ]
    
    tags_add = []
    for pattern in tag_add_patterns:
        match = re.search(pattern, text)
        if match:
            tags_add.append(match.group(1).strip())
    
    # Build confirmation text
    changes = []
    if company:
        changes.append(f"company changed to {company}")
    if role:
        changes.append(f"role changed to {role}")
    if city:
        changes.append(f"city changed to {city}")
    if tags_add:
        changes.append(f"added tags: {', '.join(tags_add)}")
    
    if changes:
        confirmation_text = f"I understand: {', '.join(changes)}. Reply YES to confirm these changes."
        confidence = 0.6 if len(changes) == 1 else 0.4
    else:
        confirmation_text = "I'm not sure I understood your update. Could you please provide more specific details?"
        confidence = 0.2
    
    return {
        "intent": "update",
        "company": company,
        "role": role,
        "city": city,
        "tags_add": tags_add,
        "confidence": confidence,
        "confirmation_text": confirmation_text
    }

def extract_phone_number(text: str) -> Optional[str]:
    """
    Extract phone number from text using regex
    
    Args:
        text: Text that may contain a phone number
        
    Returns:
        Extracted phone number or None
    """
    # Various phone number patterns
    patterns = [
        r'\+?1?\s*\(?(\d{3})\)?\s*-?\s*(\d{3})\s*-?\s*(\d{4})',  # (555) 123-4567 or 555-123-4567
        r'\+?1\s*(\d{10})',  # +1 5551234567
        r'(\d{10})',  # 5551234567
        r'\+?(\d{11})',  # +15551234567
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            if len(match.groups()) == 3:
                # Format: (555) 123-4567
                return f"+1{match.group(1)}{match.group(2)}{match.group(3)}"
            else:
                # Format: 5551234567 or +15551234567
                number = match.group(1)
                if number.startswith('1') and len(number) == 11:
                    return f"+{number}"
                elif len(number) == 10:
                    return f"+1{number}"
                else:
                    return f"+{number}"
    
    return None

def is_valid_email(text: str) -> bool:
    """
    Basic email validation using regex
    
    Args:
        text: Text to check if it's a valid email
        
    Returns:
        True if valid email format, False otherwise
    """
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(email_pattern, text))

def extract_urls(text: str) -> list:
    """
    Extract URLs from text using regex
    
    Args:
        text: Text that may contain URLs
        
    Returns:
        List of extracted URLs
    """
    url_pattern = r'https?://(?:[-\w.])+(?:[:\d]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:#(?:[\w.])*)?)?'
    return re.findall(url_pattern, text)

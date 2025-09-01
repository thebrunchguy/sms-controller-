import os
from typing import Optional
from twilio.rest import Client
from twilio.base.exceptions import TwilioException

# Twilio configuration
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")
TWILIO_MESSAGING_SERVICE_SID = os.getenv("TWILIO_MESSAGING_SERVICE_SID")

# Initialize Twilio client
twilio_client = None

def _get_twilio_client():
    """Get or initialize Twilio client"""
    global twilio_client
    if twilio_client is None:
        # Get current environment variables (they might have been loaded after module import)
        account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        
        if account_sid and auth_token:
            twilio_client = Client(account_sid, auth_token)
        else:
            print("Twilio credentials not available")
    return twilio_client

def send_sms(to: str, body: str, status_callback_url: Optional[str] = None) -> Optional[str]:
    """
    Send SMS via Twilio
    
    Args:
        to: Phone number to send to (E.164 format)
        body: Message body
        status_callback_url: Optional webhook URL for delivery status
        
    Returns:
        Message SID if successful, None if failed
    """
    client = _get_twilio_client()
    if not client:
        print("Twilio client not initialized - check environment variables")
        return None
    
    try:
        # Prepare message parameters
        message_params = {
            "to": to,
            "body": body
        }
        
        # Use messaging service if available, otherwise use phone number
        messaging_service_sid = os.getenv("TWILIO_MESSAGING_SERVICE_SID")
        phone_number = os.getenv("TWILIO_PHONE_NUMBER")
        
        if messaging_service_sid:
            message_params["messaging_service_sid"] = messaging_service_sid
        elif phone_number:
            message_params["from_"] = phone_number
        else:
            print("No Twilio phone number or messaging service configured")
            return None
        
        # Add status callback if provided
        if status_callback_url:
            message_params["status_callback"] = status_callback_url
        
        # Send the message
        message = client.messages.create(**message_params)
        
        print(f"SMS sent successfully to {to}, SID: {message.sid}")
        return message.sid
        
    except TwilioException as e:
        print(f"Twilio error sending SMS to {to}: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error sending SMS to {to}: {e}")
        return None

def validate_webhook_signature(request_body: str, signature: str, url: str) -> bool:
    """
    Validate Twilio webhook signature for security
    
    Args:
        request_body: Raw request body
        signature: X-Twilio-Signature header value
        url: Full webhook URL
        
    Returns:
        True if signature is valid, False otherwise
    """
    try:
        from twilio.request_validator import RequestValidator
        
        if not TWILIO_AUTH_TOKEN:
            print("No Twilio auth token available for signature validation")
            return False
        
        validator = RequestValidator(TWILIO_AUTH_TOKEN)
        return validator.validate(url, request_body, signature)
        
    except ImportError:
        print("twilio package not available for signature validation")
        return False
    except Exception as e:
        print(f"Error validating Twilio signature: {e}")
        return False

def format_phone_number(phone: str) -> str:
    """
    Format phone number to E.164 format
    
    Args:
        phone: Raw phone number
        
    Returns:
        Formatted E.164 phone number
    """
    # Remove all non-digit characters
    digits = ''.join(filter(str.isdigit, phone))
    
    # If it's a 10-digit US number, add +1
    if len(digits) == 10:
        return f"+1{digits}"
    
    # If it's already 11 digits and starts with 1, add +
    elif len(digits) == 11 and digits.startswith('1'):
        return f"+{digits}"
    
    # If it's already in international format, return as is
    elif digits.startswith('1') and len(digits) == 11:
        return f"+{digits}"
    
    # Otherwise, assume it's already formatted
    return phone

def get_message_status(message_sid: str) -> Optional[dict]:
    """
    Get the current status of a message
    
    Args:
        message_sid: Twilio message SID
        
    Returns:
        Dictionary with message status info, or None if failed
    """
    client = _get_twilio_client()
    if not client:
        return None
    
    try:
        message = client.messages(message_sid).fetch()
        return {
            "sid": message.sid,
            "status": message.status,
            "direction": message.direction,
            "from": message.from_,
            "to": message.to,
            "body": message.body,
            "date_sent": message.date_sent,
            "error_code": message.error_code,
            "error_message": message.error_message
        }
    except TwilioException as e:
        print(f"Error fetching message status for {message_sid}: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error fetching message status for {message_sid}: {e}")
        return None

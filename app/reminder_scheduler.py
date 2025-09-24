import os
import httpx
from datetime import datetime, timedelta
from typing import List, Dict, Any
from . import airtable, twilio_utils
from dotenv import load_dotenv

# Load environment variables
load_dotenv('config/config.env')

class ReminderScheduler:
    """Handles checking and sending reminder notifications"""
    
    def __init__(self):
        self.check_interval_minutes = 5  # Check every 5 minutes
        self.reminder_buffer_minutes = 2  # Send reminders 2 minutes before due time
    
    def get_due_reminders(self) -> List[Dict[str, Any]]:
        """Get reminders that are due to be sent"""
        try:
            # Get all reminders from the reminders table
            endpoint = f"{os.getenv('AIRTABLE_REMINDERS_TABLE')}"
            base_url = f"https://api.airtable.com/v0/{os.getenv('AIRTABLE_REMINDERS_BASE_ID')}"
            
            # Get reminders that are due within the next few minutes
            now = datetime.now()
            buffer_time = now + timedelta(minutes=self.reminder_buffer_minutes)
            
            # Filter for reminders due soon
            filter_formula = f"AND({{Due date}} <= '{buffer_time.strftime('%Y-%m-%dT%H:%M:%S')}', {{Status}} != 'Sent', {{Status}} != 'Completed')"
            
            response = airtable._make_request("GET", endpoint, params={"filterByFormula": filter_formula}, base_url=base_url)
            return response.get("records", [])
            
        except Exception as e:
            print(f"Error getting due reminders: {e}")
            return []
    
    def send_reminder_notification(self, reminder: Dict[str, Any]) -> bool:
        """Send SMS notification for a reminder"""
        try:
            fields = reminder.get("fields", {})
            reminder_text = fields.get("Reminder", "")
            due_date = fields.get("Due date", "")
            
            # Get the person's phone number from the linked person record
            person_links = fields.get("Reminders Main View", [])
            if not person_links:
                print(f"No person linked to reminder: {reminder.get('id')}")
                return False
            
            # Get person details
            person_id = person_links[0]  # Get first linked person
            person_endpoint = f"{os.getenv('AIRTABLE_REMINDERS_MAIN_PEOPLE_TABLE')}/{person_id}"
            base_url = f"https://api.airtable.com/v0/{os.getenv('AIRTABLE_REMINDERS_BASE_ID')}"
            
            person_response = airtable._make_request("GET", person_endpoint, base_url=base_url)
            person_fields = person_response.get("fields", {})
            person_name = person_fields.get("Name", "Unknown")
            phone = person_fields.get("Phone", "")
            
            if not phone:
                print(f"No phone number for {person_name}")
                return False
            
            # Format phone number
            phone = phone.replace("(", "").replace(")", "").replace("-", "").replace(" ", "")
            if not phone.startswith("+1"):
                phone = f"+1{phone}"
            
            # Create notification message
            notification_message = f"🔔 Reminder: {reminder_text}"
            if due_date:
                try:
                    due_dt = datetime.fromisoformat(due_date.replace('Z', '+00:00'))
                    time_str = due_dt.strftime('%I:%M %p')
                    notification_message += f" (due at {time_str})"
                except:
                    pass
            
            # Send SMS to your admin number
            admin_phone = os.getenv("ADMIN_PHONE_NUMBER", "9784910236")
            if not admin_phone.startswith("+1"):
                admin_phone = f"+1{admin_phone}"
            
            twilio_sid = twilio_utils.send_sms(
                to=admin_phone,
                body=notification_message,
                status_callback_url=f"{os.getenv('APP_BASE_URL', 'http://localhost:8000')}/twilio/status"
            )
            
            if twilio_sid:
                # Mark reminder as sent
                self.mark_reminder_sent(reminder.get("id"))
                print(f"✅ Sent reminder notification: {reminder_text}")
                return True
            else:
                print(f"❌ Failed to send reminder notification: {reminder_text}")
                return False
                
        except Exception as e:
            print(f"Error sending reminder notification: {e}")
            return False
    
    def mark_reminder_sent(self, reminder_id: str) -> bool:
        """Mark a reminder as sent"""
        try:
            endpoint = f"{os.getenv('AIRTABLE_REMINDERS_TABLE')}/{reminder_id}"
            base_url = f"https://api.airtable.com/v0/{os.getenv('AIRTABLE_REMINDERS_BASE_ID')}"
            
            update_data = {
                "fields": {
                    "Status": "Sent",
                    "Sent At": datetime.now().isoformat()
                }
            }
            
            airtable._make_request("PATCH", endpoint, update_data, base_url=base_url)
            return True
            
        except Exception as e:
            print(f"Error marking reminder as sent: {e}")
            return False
    
    def process_due_reminders(self) -> Dict[str, int]:
        """Process all due reminders and send notifications"""
        due_reminders = self.get_due_reminders()
        
        sent_count = 0
        failed_count = 0
        
        for reminder in due_reminders:
            if self.send_reminder_notification(reminder):
                sent_count += 1
            else:
                failed_count += 1
        
        return {
            "total": len(due_reminders),
            "sent": sent_count,
            "failed": failed_count
        }

# Global scheduler instance
scheduler = ReminderScheduler()

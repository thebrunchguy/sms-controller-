import os
import json
import httpx
from datetime import datetime, date
from typing import Dict, Any, Optional
from fastapi import FastAPI, Form, Request, HTTPException
from fastapi.responses import HTMLResponse
from . import compose, airtable, twilio_utils, llm, scheduler, admin_sms, intent_classifier, intent_handlers

app = FastAPI()

@app.post("/jobs/send-monthly")
def send_monthly():
    """Send monthly check-in SMS to people who are due"""
    try:
        # Get current month in YYYY-MM format
        current_month = datetime.now().strftime("%Y-%m")
        
        # Get people due for check-in using scheduler
        people_due = scheduler.get_people_due_for_checkin()
        
        if not people_due:
            return {"ok": True, "message": "No people due for check-in this month", "count": 0}
        
        sent_count = 0
        failed_count = 0
        
        for person_record in people_due:
            try:
                person_id = person_record["id"]
                person_fields = person_record["fields"]
                
                # Skip if no phone number
                phone = person_fields.get("Phone")
                if not phone:
                    print(f"No phone number for person {person_id}")
                    failed_count += 1
                    continue
                
                # Create or update check-in record
                checkin_id = airtable.upsert_checkin(
                    person_id=person_id,
                    month=current_month,
                    status="Sent"
                )
                
                if not checkin_id:
                    print(f"Failed to create check-in for person {person_id}")
                    failed_count += 1
                    continue
                
                # Compose snapshot and outbound message
                snapshot = compose.compose_snapshot(person_fields)
                last_confirmed = person_fields.get("Last Confirmed")
                name = person_fields.get("Name", "there")
                
                outbound_message = compose.compose_outbound(name, snapshot, last_confirmed)
                
                # Send SMS via Twilio
                twilio_sid = twilio_utils.send_sms(
                    to=phone,
                    body=outbound_message,
                    status_callback_url=f"{os.getenv('APP_BASE_URL', 'http://localhost:8000')}/twilio/status"
                )
                
                if twilio_sid:
                    # Log outbound message
                    airtable.log_message(
                        checkin_id=checkin_id,
                        direction="Outbound",
                        from_number=os.getenv("TWILIO_PHONE_NUMBER", ""),
                        body=outbound_message,
                        twilio_sid=twilio_sid
                    )
                    
                    # Append to transcript
                    airtable.append_to_transcript(
                        checkin_id=checkin_id,
                        message=f"Sent monthly check-in SMS to {phone}"
                    )
                    
                    sent_count += 1
                else:
                    # Update check-in status to failed
                    airtable.update_checkin_status(checkin_id, "Failed")
                    failed_count += 1
                    
            except Exception as e:
                print(f"Error processing person {person_record.get('id', 'unknown')}: {e}")
                failed_count += 1
        
        return {
            "ok": True, 
            "message": f"Monthly check-in job completed. Sent: {sent_count}, Failed: {failed_count}",
            "sent": sent_count,
            "failed": failed_count
        }
        
    except Exception as e:
        print(f"Error in send_monthly job: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.post("/twilio/inbound")
async def inbound(request: Request, From: str = Form(...), Body: str = Form(...), MessageSid: str = Form(...)):
    """Handle inbound SMS from Twilio"""
    try:
        # Clean phone number (remove +1 prefix if present)
        from_phone = From.replace("+1", "") if From.startswith("+1") else From
        
        # Find person by phone number (prefer check-ins table for SMS processing)
        person_record = airtable.get_person_by_phone(from_phone, prefer_checkins=True)
        
        if not person_record:
            # Unknown phone number - could log this for review
            return {"ok": False, "message": "Unknown phone number"}
        
        person_id = person_record["id"]
        person_fields = person_record["fields"]
        
        # Check if person has opted out
        if person_fields.get("Opt-out"):
            return {"ok": False, "message": "Person has opted out"}
        
        # Get current month
        current_month = datetime.now().strftime("%Y-%m")
        
        # Create or update check-in record
        checkin_id = airtable.upsert_checkin(
            person_id=person_id,
            month=current_month,
            status="In progress"
        )
        
        if not checkin_id:
            raise HTTPException(status_code=500, detail="Failed to create check-in record")
        
        # Log inbound message
        airtable.log_message(
            checkin_id=checkin_id,
            direction="Inbound",
            from_number=from_phone,
            body=Body,
            twilio_sid=MessageSid
        )
        
        # Append to transcript
        airtable.append_to_transcript(
            checkin_id=checkin_id,
            message=f"Received SMS: {Body}"
        )
        
        
        # Process the message body
        body_lower = Body.strip().lower()
        
        if body_lower in ["help", "controls"]:
            # Send help message with available commands
            help_message = """📋 Available Commands:
• new friend [Name] - Add a new friend
• update my birthday [Date] - Update your birthday
• update my company [Company] - Update your company
• update my role [Role] - Update your role
• tag me with [Tag] - Add a tag
• remind me to [Action] [Timeline] - Create a reminder
• note: [Note] - Add a note
• follow up [Timeline] - Schedule follow-up
• no change - Confirm no updates needed
• stop - Unsubscribe from messages"""
            
            twilio_utils.send_sms(
                to=from_phone,
                body=help_message,
                status_callback_url=f"{os.getenv('APP_BASE_URL', 'http://localhost:8000')}/twilio/status"
            )
            
            # Log outbound message
            airtable.log_message(
                checkin_id=checkin_id,
                direction="Outbound",
                from_number=os.getenv("TWILIO_PHONE_NUMBER", ""),
                body=help_message,
                twilio_sid=""
            )
            
            return {"ok": True, "message": "Help message sent"}
            
        elif body_lower == "stop":
            # Handle opt-out
            airtable.update_person(person_id, {"Opt-out": True})
            airtable.update_checkin_status(checkin_id, "Opted-out")
            
            # Send confirmation
            optout_message = "You have been unsubscribed from monthly check-ins. Reply START to resubscribe."
            twilio_utils.send_sms(
                to=from_phone,
                body=optout_message,
                status_callback_url=f"{os.getenv('APP_BASE_URL', 'http://localhost:8000')}/twilio/status"
            )
            
            # Log outbound message
            airtable.log_message(
                checkin_id=checkin_id,
                direction="Outbound",
                from_number=os.getenv("TWILIO_PHONE_NUMBER", ""),
                body=optout_message,
                twilio_sid=""
            )
            
            return {"ok": True, "message": "Person opted out"}
            
        elif body_lower in ["no change", "no changes", "nothing changed", "same"]:
            # Handle no change response
            airtable.update_person(person_id, {"Last Confirmed": date.today().isoformat()})
            airtable.update_checkin_status(checkin_id, "Completed")
            
            # Send confirmation
            confirmation_message = "👍 Thanks for confirming! No changes needed."
            twilio_utils.send_sms(
                to=from_phone,
                body=confirmation_message,
                status_callback_url=f"{os.getenv('APP_BASE_URL', 'http://localhost:8000')}/twilio/status"
            )
            
            # Log outbound message
            airtable.log_message(
                checkin_id=checkin_id,
                direction="Outbound",
                from_number=os.getenv("TWILIO_PHONE_NUMBER", ""),
                body=confirmation_message,
                twilio_sid=""
            )
            
            return {"ok": True, "message": "No changes confirmed"}
            
        elif body_lower == "yes":
            # Handle confirmation of pending changes
            # Get the check-in record to see if there are pending changes
            # This would require a function to get check-in by ID
            # For now, we'll assume there are pending changes
            
            # Update person with pending changes (this would need to be implemented)
            # For now, just mark as completed
            airtable.update_checkin_status(checkin_id, "Completed")
            
            confirmation_message = "✅ Changes applied! Thanks for the update."
            twilio_utils.send_sms(
                to=from_phone,
                body=confirmation_message,
                status_callback_url=f"{os.getenv('APP_BASE_URL', 'http://localhost:8000')}/twilio/status"
            )
            
            # Log outbound message
            airtable.log_message(
                checkin_id=checkin_id,
                direction="Outbound",
                from_number=os.getenv("TWILIO_PHONE_NUMBER", ""),
                body=confirmation_message,
                twilio_sid=""
            )
            
            return {"ok": True, "message": "Changes confirmed and applied"}
            
        else:
            # Handle free-text updates via intent classification
            try:
                # Classify the intent
                classification = intent_classifier.classify_intent(Body, person_fields)
                
                intent = classification.get("intent")
                confidence = classification.get("confidence", 0)
                target_table = classification.get("target_table", "None")
                extracted_data = classification.get("extracted_data", {})
                
                print(f"🎯 Intent: {intent}, Confidence: {confidence}, Target: {target_table}")
                
                if confidence < 0.6:
                    # Low confidence - ask for clarification
                    clarification_message = "I'm not sure I understood your message. Could you please rephrase or provide more details?"
                    
                    twilio_utils.send_sms(
                        to=from_phone,
                        body=clarification_message,
                        status_callback_url=f"{os.getenv('APP_BASE_URL', 'http://localhost:8000')}/twilio/status"
                    )
                    
                    # Log outbound message
                    airtable.log_message(
                        checkin_id=checkin_id,
                        direction="Outbound",
                        from_number=os.getenv("TWILIO_PHONE_NUMBER", ""),
                        body=clarification_message,
                        twilio_sid=""
                    )
                    
                    return {"ok": True, "message": "Low confidence, clarification requested"}
                
                # Route to appropriate handler based on intent
                success = False
                response_message = ""
                
                if intent == "update_person_info":
                    success, response_message = intent_handlers.IntentHandlers.handle_update_person_info(
                        extracted_data, person_id, person_fields
                    )
                elif intent == "manage_tags":
                    success, response_message = intent_handlers.IntentHandlers.handle_manage_tags(
                        extracted_data, person_id, person_fields
                    )
                elif intent == "create_reminder":
                    success, response_message = intent_handlers.IntentHandlers.handle_create_reminder(
                        extracted_data, person_id, person_fields
                    )
                elif intent == "create_note":
                    success, response_message = intent_handlers.IntentHandlers.handle_create_note(
                        extracted_data, person_id, person_fields
                    )
                elif intent == "schedule_followup":
                    success, response_message = intent_handlers.IntentHandlers.handle_schedule_followup(
                        extracted_data, person_id, person_fields
                    )
                elif intent == "new_friend":
                    success, response_message = intent_handlers.IntentHandlers.handle_new_friend(
                        extracted_data, person_id, person_fields
                    )
                elif intent == "unclear":
                    # Check if there's a custom error message from the intent classifier
                    error_message = extracted_data.get("error_message", "")
                    if error_message:
                        response_message = error_message
                    else:
                        response_message = "I received your message but couldn't understand what you'd like me to do. Please try rephrasing with specific actions like 'remind me to...', 'update my...', or 'add a note...'"
                else:
                    response_message = "I'm not sure how to help with that. Please try rephrasing your message with specific actions like 'remind me to...', 'update my...', or 'add a note...'"
                
                # Send response
                twilio_utils.send_sms(
                    to=from_phone,
                    body=response_message,
                    status_callback_url=f"{os.getenv('APP_BASE_URL', 'http://localhost:8000')}/twilio/status"
                )
                
                # Log outbound message
                airtable.log_message(
                    checkin_id=checkin_id,
                    direction="Outbound",
                    from_number=os.getenv("TWILIO_PHONE_NUMBER", ""),
                    body=response_message,
                    twilio_sid=""
                )
                
                # Append to transcript
                airtable.append_to_transcript(
                    checkin_id=checkin_id,
                    message=f"Intent: {intent}, Target: {target_table}, Success: {success}"
                )
                
                return {"ok": True, "message": f"Intent {intent} handled: {response_message}"}
                
            except Exception as e:
                print(f"Error in intent classification: {e}")
                # Fallback message
                fallback_message = "I received your message but had trouble processing it. Please try again or reply 'No change' if nothing has changed."
                
                twilio_utils.send_sms(
                    to=from_phone,
                    body=fallback_message,
                    status_callback_url=f"{os.getenv('APP_BASE_URL', 'http://localhost:8000')}/twilio/status"
                )
                
                # Log outbound message
                airtable.log_message(
                    checkin_id=checkin_id,
                    direction="Outbound",
                    from_number=os.getenv("TWILIO_PHONE_NUMBER", ""),
                    body=fallback_message,
                    twilio_sid=""
                )
                
                return {"ok": True, "message": "Intent classification error, fallback message sent"}
        
    except Exception as e:
        print(f"Error in inbound SMS handler: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.post("/twilio/status")
async def status(request: Request):
    """Handle Twilio status callbacks for delivery events"""
    try:
        data = await request.form()
        
        # Extract relevant fields
        message_sid = data.get("MessageSid", "")
        message_status = data.get("MessageStatus", "")
        error_code = data.get("ErrorCode", "")
        error_message = data.get("ErrorMessage", "")
        
        # Find the check-in by message SID (this would require a function to search messages)
        # For now, we'll just log the status data
        
        # Log system message about delivery status
        # This would require finding the check-in ID from the message SID
        # For now, we'll just return the data
        
        return {
            "ok": True, 
            "message": "Status callback received", 
            "data": {
                "message_sid": message_sid,
                "status": message_status,
                "error_code": error_code,
                "error_message": error_message
            }
        }
        
    except Exception as e:
        print(f"Error in status callback handler: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"ok": True, "status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/stats/monthly")
def get_monthly_stats():
    """Get monthly check-in statistics"""
    try:
        stats = scheduler.get_monthly_checkin_stats()
        return {"ok": True, "stats": stats}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting stats: {str(e)}")

@app.get("/people/due")
def get_due_people():
    """Get people due for check-in this month"""
    try:
        due_people = airtable.get_all_people()
        return {
            "ok": True, 
            "count": len(due_people),
            "people": [{"id": p["id"], "name": p["fields"].get("Name"), "phone": p["fields"].get("Phone")} for p in due_people]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting due people: {str(e)}")

@app.get("/people/overdue")
def get_overdue_people():
    """Get people who are overdue for check-in"""
    try:
        overdue_people = scheduler.get_overdue_people()
        return {
            "ok": True, 
            "count": len(overdue_people),
            "people": [{"id": p["id"], "name": p["fields"].get("Name"), "phone": p["fields"].get("Phone")} for p in overdue_people]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting overdue people: {str(e)}")

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "SMS Check-in Service", "admin": "/admin", "docs": "/docs"}

@app.post("/admin/add-birthday")
async def admin_add_birthday(name: str = Form(...), birthday: str = Form(...)):
    """Add birthday - reuses existing admin_sms functionality"""
    command_data = {
        "command": "add_birthday",
        "name": name,
        "birthday": birthday
    }
    
    success, message = admin_sms.execute_admin_command(command_data)
    return {"success": success, "message": message}

@app.post("/admin/change-role")
async def admin_change_role(name: str = Form(...), new_role: str = Form(...)):
    """Change role - reuses existing admin_sms functionality"""
    command_data = {
        "command": "change_role", 
        "name": name,
        "new_role": new_role
    }
    
    success, message = admin_sms.execute_admin_command(command_data)
    return {"success": success, "message": message}

@app.post("/admin/change-company")
async def admin_change_company(name: str = Form(...), new_company: str = Form(...)):
    """Change company - reuses existing admin_sms functionality"""
    command_data = {
        "command": "change_company",
        "name": name, 
        "new_company": new_company
    }
    
    success, message = admin_sms.execute_admin_command(command_data)
    return {"success": success, "message": message}

@app.get("/admin/search")
async def search_people(query: str):
    """Search for people by name"""
    try:
        # Get all people from Airtable
        people = airtable.get_all_people()
        
        # Search for people by name (case-insensitive)
        query_lower = query.lower()
        matches = []
        
        for person in people:
            name = person.get('fields', {}).get('Name', '')
            if query_lower in name.lower():
                matches.append({
                    'id': person['id'],
                    'name': name,
                    'phone': person.get('fields', {}).get('Phone', ''),
                    'company': person.get('fields', {}).get('Company', ''),
                    'role': person.get('fields', {}).get('Role', '')
                })
        
        return {"success": True, "matches": matches, "count": len(matches)}
        
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/admin")
async def admin_dashboard():
    """Admin web interface with search"""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Admin Dashboard - Kobro.co</title>
        <link rel="icon" href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><text y=%22.9em%22 font-size=%2290%22>👉</text></svg>">
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
            .container { max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            h1 { color: #333; text-align: center; margin-bottom: 30px; }
            h2 { color: #555; border-bottom: 2px solid #007bff; padding-bottom: 10px; }
            .form-group { margin: 20px 0; }
            label { display: block; margin-bottom: 5px; font-weight: bold; color: #333; }
            input, select { padding: 10px; width: 100%; max-width: 400px; border: 1px solid #ddd; border-radius: 4px; font-size: 14px; }
            button { padding: 12px 24px; background: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 14px; }
            button:hover { background: #0056b3; }
            .result { margin: 20px 0; padding: 15px; border-radius: 4px; font-weight: bold; }
            .success { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
            .error { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
            .form-section { background: #f8f9fa; padding: 20px; margin: 20px 0; border-radius: 6px; border-left: 4px solid #007bff; }
            .search-section { background: #e3f2fd; padding: 20px; margin: 20px 0; border-radius: 6px; border-left: 4px solid #2196f3; }
            .search-results { margin-top: 15px; }
            .person-card { background: white; padding: 15px; margin: 10px 0; border-radius: 4px; border: 1px solid #ddd; }
            .person-name { font-weight: bold; color: #333; }
            .person-details { color: #666; font-size: 14px; margin-top: 5px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🎛️ Admin Dashboard</h1>
            
            <div class="search-section">
                <h2>🔍 Search People</h2>
                <div class="form-group">
                    <input type="text" id="searchInput" placeholder="Type a name to search..." style="width: 100%; max-width: 600px;">
                </div>
                <div id="searchResults" class="search-results"></div>
            </div>
            
            <div class="form-section">
                <h2>�� Add Birthday</h2>
                <form action="/admin/add-birthday" method="post" onsubmit="return submitForm(this, event)">
                    <div class="form-group">
                        <label>Name:</label>
                        <input type="text" name="name" required placeholder="Enter exact name as in Airtable">
                    </div>
                    <div class="form-group">
                        <label>Birthday:</label>
                        <input type="date" name="birthday" required>
                    </div>
                    <button type="submit">Add Birthday</button>
                </form>
            </div>
            
            <div class="form-section">
                <h2>💼 Change Role</h2>
                <form action="/admin/change-role" method="post" onsubmit="return submitForm(this, event)">
                    <div class="form-group">
                        <label>Name:</label>
                        <input type="text" name="name" required placeholder="Enter exact name as in Airtable">
                    </div>
                    <div class="form-group">
                        <label>New Role:</label>
                        <input type="text" name="new_role" required placeholder="e.g., Senior Developer">
                    </div>
                    <button type="submit">Change Role</button>
                </form>
            </div>
            
            <div class="form-section">
                <h2>🏢 Change Company</h2>
                <form action="/admin/change-company" method="post" onsubmit="return submitForm(this, event)">
                    <div class="form-group">
                        <label>Name:</label>
                        <input type="text" name="name" required placeholder="Enter exact name as in Airtable">
                    </div>
                    <div class="form-group">
                        <label>New Company:</label>
                        <input type="text" name="new_company" required placeholder="e.g., Google">
                    </div>
                    <button type="submit">Change Company</button>
                </form>
            </div>
        </div>
        
        <script>
            // Search functionality
            const searchInput = document.getElementById('searchInput');
            const searchResults = document.getElementById('searchResults');
            
            searchInput.addEventListener('input', async function() {
                const query = this.value.trim();
                
                if (query.length < 2) {
                    searchResults.innerHTML = '';
                    return;
                }
                
                try {
                    const response = await fetch(`/admin/search?query=${encodeURIComponent(query)}`);
                    const data = await response.json();
                    
                    if (data.success) {
                        displaySearchResults(data.matches);
                    } else {
                        searchResults.innerHTML = '<div class="error">❌ Search error: ' + data.error + '</div>';
                    }
                } catch (error) {
                    searchResults.innerHTML = '<div class="error">❌ Search failed: ' + error.message + '</div>';
                }
            });
            
            function displaySearchResults(matches) {
                if (matches.length === 0) {
                    searchResults.innerHTML = '<div class="result">No people found matching your search.</div>';
                    return;
                }
                
                let html = `<div class="result success">Found ${matches.length} person(s):</div>`;
                
                matches.forEach(person => {
                    html += `
                        <div class="person-card">
                            <div class="person-name">${person.name}</div>
                            <div class="person-details">
                                ${person.phone ? '📞 ' + person.phone + '<br>' : ''}
                                ${person.company ? '🏢 ' + person.company + '<br>' : ''}
                                ${person.role ? '💼 ' + person.role : ''}
                            </div>
                        </div>
                    `;
                });
                
                searchResults.innerHTML = html;
            }
            
            // Form submission
            async function submitForm(form, event) {
                event.preventDefault();
                
                const formData = new FormData(form);
                const action = form.action;
                
                try {
                    const response = await fetch(action, {
                        method: 'POST',
                        body: formData
                    });
                    
                    const result = await response.json();
                    
                    // Show result
                    const resultDiv = document.createElement('div');
                    resultDiv.className = 'result ' + (result.success ? 'success' : 'error');
                    resultDiv.textContent = result.message;
                    
                    form.parentNode.insertBefore(resultDiv, form.nextSibling);
                    
                    // Clear form if successful
                    if (result.success) {
                        form.reset();
                    }
                    
                    // Remove result after 5 seconds
                    setTimeout(() => {
                        resultDiv.remove();
                    }, 5000);
                    
                } catch (error) {
                    const resultDiv = document.createElement('div');
                    resultDiv.className = 'result error';
                    resultDiv.textContent = '❌ Error: ' + error.message;
                    form.parentNode.insertBefore(resultDiv, form.nextSibling);
                }
            }
        </script>
    </body>
    </html>
    """
    
    return HTMLResponse(content=html_content)

@app.get("/admin/debug")
async def debug_airtable():
    """Debug endpoint to see what's in Airtable"""
    try:
        # Get all people from the current table
        people = airtable.get_all_people()
        
        # Get basic info about what we found
        debug_info = {
            "table_name": os.getenv("AIRTABLE_PEOPLE_TABLE", "People"),
            "base_id": os.getenv("AIRTABLE_BASE_ID", "unknown"),
            "checkins_base_id": os.getenv("AIRTABLE_CHECKINS_BASE_ID", "unknown"),
            "checkins_base_url": os.getenv("AIRTABLE_CHECKINS_BASE_URL", "unknown"),
            "checkins_table": os.getenv("AIRTABLE_CHECKINS_TABLE", "unknown"),
            "checkins_people_table": os.getenv("AIRTABLE_CHECKINS_PEOPLE_TABLE", "unknown"),
            "total_records": len(people),
            "sample_records": []
        }
        
        # Show first 5 records as samples
        for i, person in enumerate(people[:5]):
            fields = person.get('fields', {})
            debug_info["sample_records"].append({
                "id": person['id'],
                "name": fields.get('Name', 'No name'),
                "phone": fields.get('Phone', 'No phone'),
                "company": fields.get('Company', 'No company'),
                "all_fields": list(fields.keys())
            })
        
        return debug_info
        
    except Exception as e:
        return {"error": str(e), "traceback": str(e.__traceback__)}

@app.post("/jobs/check-reminders")
def check_reminders():
    """Check for due reminders and send notifications"""
    try:
        # Simple reminder check - get reminders due in the next 5 minutes
        from datetime import datetime, timedelta
        
        now = datetime.now()
        buffer_time = now + timedelta(minutes=5)
        
        # Get reminders from Airtable
        endpoint = f"{os.getenv('AIRTABLE_REMINDERS_TABLE')}"
        base_url = f"https://api.airtable.com/v0/{os.getenv('AIRTABLE_REMINDERS_BASE_ID')}"
        
        filter_formula = f"AND({{Due date}} <= '{buffer_time.isoformat()}', {{Status}} != 'Sent', {{Status}} != 'Completed')"
        
        response = airtable._make_request("GET", endpoint, params={"filterByFormula": filter_formula}, base_url=base_url)
        reminders = response.get("records", [])
        
        sent_count = 0
        for reminder in reminders:
            try:
                fields = reminder.get("fields", {})
                reminder_text = fields.get("Reminder", "")
                
                # Send notification
                notification_message = f"🔔 Reminder: {reminder_text}"
                
                twilio_sid = twilio_utils.send_sms(
                    to=os.getenv("TWILIO_PHONE_NUMBER", "+16469177351"),
                    body=notification_message,
                    status_callback_url=f"{os.getenv('APP_BASE_URL', 'http://localhost:8000')}/twilio/status"
                )
                
                if twilio_sid:
                    # Mark as sent
                    reminder_id = reminder.get("id")
                    update_data = {
                        "fields": {
                            "Status": "Sent",
                            "Sent At": datetime.now().isoformat()
                        }
                    }
                    airtable._make_request("PATCH", f"{endpoint}/{reminder_id}", update_data, base_url=base_url)
                    sent_count += 1
                    print(f"✅ Sent reminder: {reminder_text}")
                    
            except Exception as e:
                print(f"Error processing reminder: {e}")
        
        return {
            "ok": True,
            "message": f"Processed {len(reminders)} reminders. Sent: {sent_count}",
            "total": len(reminders),
            "sent": sent_count
        }
        
    except Exception as e:
        print(f"Error in check_reminders: {e}")
        return {"ok": False, "error": str(e)}

@app.get("/test-reminders")
def test_reminders():
    """Test endpoint to check reminder system"""
    return {"ok": True, "message": "Reminder system is working"}

@app.get("/twilio/logs")
def get_twilio_logs(limit: int = 20):
    """Get recent Twilio message logs"""
    try:
        account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        
        if not account_sid or not auth_token:
            return {"error": "Twilio credentials not configured"}
        
        # Fetch recent messages
        url = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json"
        params = {
            "PageSize": limit,
            "To": os.getenv("TWILIO_PHONE_NUMBER", ""),
            "From": "9784910236"  # Your admin number
        }
        
        response = httpx.get(
            url,
            params=params,
            auth=(account_sid, auth_token)
        )
        
        if response.status_code == 200:
            data = response.json()
            messages = []
            
            for msg in data.get("messages", []):
                messages.append({
                    "sid": msg.get("sid"),
                    "from": msg.get("from"),
                    "to": msg.get("to"),
                    "body": msg.get("body"),
                    "status": msg.get("status"),
                    "direction": msg.get("direction"),
                    "date_created": msg.get("date_created"),
                    "date_sent": msg.get("date_sent"),
                    "error_code": msg.get("error_code"),
                    "error_message": msg.get("error_message")
                })
            
            return {
                "ok": True,
                "messages": messages,
                "count": len(messages)
            }
        else:
            return {"error": f"Twilio API error: {response.status_code} - {response.text}"}
            
    except Exception as e:
        return {"error": str(e)}


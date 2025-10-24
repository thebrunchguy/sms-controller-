# Command Processing Logic

This document describes the step-by-step logic for processing each type of SMS command once the intent is classified.

## Overview

All SMS commands follow this general flow:
1. **Phone Lookup**: Find person by phone number
2. **Check-in Creation**: Create/update monthly check-in record
3. **Intent Classification**: Determine what the user wants to do
4. **Command Execution**: Execute the specific action
5. **Response**: Send confirmation back to user

## Phone Lookup Process

### Step 1: Normalize Phone Number
- Remove `+1` prefix if present
- Example: `+19784910236` → `9784910236`

### Step 2: Find Person in Main Base
- Search `AIRTABLE_BASE_ID` (appCA6OJqDxLdiEqf) People table
- Look for matching phone number (case-insensitive)
- If found: Get person record with ID and fields

### Step 3: Find Mirror in Check-ins Base
- Search `AIRTABLE_CHECKINS_BASE_ID` (apptiPfA1VJX5fEZ2) People table
- Look for person with same name (case-insensitive)
- Handle pagination to search all records
- If found: Use check-ins base person ID
- If not found: Use main base person ID

## Check-in Creation Process

### Step 1: Create Monthly Check-in Record
- Table: `AIRTABLE_CHECKINS_TABLE` (tblivVAPP95ccK8xL)
- Base: `AIRTABLE_CHECKINS_BASE_ID` (apptiPfA1VJX5fEZ2)
- Fields:
  - `Person`: [person_id_from_checkins_base]
  - `Status`: "Sent"
  - `Month`: Current month (YYYY-MM format)

### Step 2: Log Inbound Message
- Table: Messages table
- Fields:
  - `Check-in`: [checkin_id]
  - `Direction`: "Inbound"
  - `From Number`: [phone_number]
  - `Body`: [message_text]
  - `Twilio SID`: [message_sid]

## Command-Specific Processing

### 1. "new friend [Name]" Command

**Intent**: `new_friend`
**Target Table**: Core People

#### Process:
1. **Extract Friend Name**
   - Parse name from message using intent classifier
   - Example: "new friend William Murray" → "William Murray"

2. **Check if Person Already Exists**
   - Search main People table by name (case-insensitive)
   - If found: Return error "Person already exists"

3. **Create New Person Record**
   - Table: `AIRTABLE_BASE_ID` (appCA6OJqDxLdiEqf) People table
   - Fields:
     - `Name`: [extracted_name]
   - Return: New person ID

4. **Response**
   - Success: "✅ Added new friend '[Name]' to Airtable"
   - Error: "❌ Failed to create new friend '[Name]'"

#### Airtable Links:
- Main People Table: https://airtable.com/appCA6OJqDxLdiEqf/tbl2pDRalUQpzEBkQ

---

### 2. "update [Name] birthday [Date]" Command

**Intent**: `update_person_info`
**Target Table**: Core People

#### Process:
1. **Extract Update Data**
   - Parse person name and birthday from message
   - Example: "update John birthday 1990-05-15" → Name: "John", Birthday: "1990-05-15"

2. **Find Person in Main Table**
   - Search by name (case-insensitive)
   - If not found: Return error "Person not found"

3. **Update Person Record**
   - Table: `AIRTABLE_BASE_ID` (appCA6OJqDxLdiEqf) People table
   - Fields:
     - `Birthday`: [parsed_date]

4. **Response**
   - Success: "✅ Updated [Name]'s birthday to [Date]"
   - Error: "❌ Person '[Name]' not found" or "❌ Failed to update birthday"

---

### 3. "add tag [Tag] to [Name]" Command

**Intent**: `manage_tags`
**Target Table**: Core People

#### Process:
1. **Extract Tag and Person**
   - Parse tag name and person name
   - Example: "add tag friend to John" → Tag: "friend", Person: "John"

2. **Find Person in Main Table**
   - Search by name (case-insensitive)

3. **Update Tags Field**
   - Add new tag to existing tags array
   - Handle comma-separated tags

4. **Response**
   - Success: "✅ Added tag '[Tag]' to [Name]"
   - Error: "❌ Person '[Name]' not found"

---

### 4. "remind me to [Task] [Timeline]" Command

**Intent**: `create_reminder`
**Target Table**: Reminders

#### Process:
1. **Extract Reminder Data**
   - Parse task description and timeline
   - Example: "remind me to call John next week" → Task: "call John", Timeline: "next week"

2. **Create Reminder Record**
   - Table: `AIRTABLE_BASE_ID` (appCA6OJqDxLdiEqf) Reminders table
   - Fields:
     - `Task`: [task_description]
     - `Timeline`: [timeline]
     - `Person`: [person_id]
     - `Status`: "Pending"

3. **Response**
   - Success: "✅ Created reminder: [Task] ([Timeline])"
   - Error: "❌ Failed to create reminder"

---

### 5. "add note [Content] for [Name]" Command

**Intent**: `create_note`
**Target Table**: Notes

#### Process:
1. **Extract Note Data**
   - Parse note content and person name
   - Example: "add note met at conference for John" → Content: "met at conference", Person: "John"

2. **Find Person in Main Table**
   - Search by name (case-insensitive)

3. **Create Note Record**
   - Table: `AIRTABLE_BASE_ID` (appCA6OJqDxLdiEqf) Notes table
   - Fields:
     - `Content`: [note_content]
     - `Person`: [person_id]
     - `Date`: Current date

4. **Response**
   - Success: "✅ Added note for [Name]: [Content]"
   - Error: "❌ Person '[Name]' not found"

---

### 6. "schedule followup [Timeline] for [Name]" Command

**Intent**: `schedule_followup`
**Target Table**: Follow-ups

#### Process:
1. **Extract Follow-up Data**
   - Parse timeline and person name
   - Example: "schedule followup next month for John" → Timeline: "next month", Person: "John"

2. **Find Person in Main Table**
   - Search by name (case-insensitive)

3. **Create Follow-up Record**
   - Table: `AIRTABLE_BASE_ID` (appCA6OJqDxLdiEqf) Follow-ups table
   - Fields:
     - `Person`: [person_id]
     - `Timeline`: [timeline]
     - `Status`: "Scheduled"
     - `Scheduled Date`: Calculate based on timeline

4. **Response**
   - Success: "✅ Scheduled follow-up for [Name] ([Timeline])"
   - Error: "❌ Person '[Name]' not found"

---

## Special Commands

### "controls" or "help" Command

**Process:**
1. **Skip Person Lookup** - Works even without person record
2. **Send Help Message** - Predefined list of available commands
3. **No Check-in Creation** - Bypasses normal flow

### "stop" Command

**Process:**
1. **Find Person** - Normal phone lookup
2. **Update Opt-out Status** - Set `Opt-out: True` in People table
3. **Update Check-in Status** - Set check-in status to "Opted-out"
4. **Send Confirmation** - "You have been unsubscribed..."

### "no change" Command

**Process:**
1. **Find Person** - Normal phone lookup
2. **Update Last Confirmed** - Set to current date
3. **Complete Check-in** - Set status to "Completed"
4. **Send Confirmation** - "Thanks for confirming! No changes needed."

---

## Error Handling

### Common Error Scenarios:
1. **Person Not Found**: "Unknown phone number" or "Person '[Name]' not found"
2. **Airtable API Error**: "Failed to create/update record"
3. **Invalid Data**: "Could not parse [field] from message"
4. **Permission Error**: "Insufficient permissions to create record"

### Fallback Responses:
- **Low Confidence Intent**: "I'm not sure I understood your message. Could you please rephrase?"
- **Unclear Intent**: "I received your message but couldn't understand what you'd like me to do."
- **System Error**: "I received your message but had trouble processing it. Please try again."

---

## Airtable Table References

### Main Base (appCA6OJqDxLdiEqf):
- **People Table**: https://airtable.com/appCA6OJqDxLdiEqf/tbl2pDRalUQpzEBkQ
- **Reminders Table**: [Table ID needed]
- **Notes Table**: [Table ID needed]
- **Follow-ups Table**: [Table ID needed]

### Check-ins Base (apptiPfA1VJX5fEZ2):
- **Check-ins Table**: https://airtable.com/apptiPfA1VJX5fEZ2/tblivVAPP95ccK8xL
- **People Table**: https://airtable.com/apptiPfA1VJX5fEZ2/tblyh3CA81E0lilm1



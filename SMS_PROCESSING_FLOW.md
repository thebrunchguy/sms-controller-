# SMS Processing Flow Diagram

## System Overview

```
📱 User Phone (9784910236) 
    ↓ SMS Message
📞 Twilio Number (+16469177351)
    ↓ Webhook
🌐 Render App (kobro-admin.onrender.com)
    ↓ Processing
🗄️ Airtable Database
    ↓ Response
📱 User Phone (Confirmation)
```

## Message Processing Flow

### 1. SMS Reception
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   User Phone    │───▶│  Twilio Number  │───▶│   Render App    │
│  (9784910236)   │    │ (+16469177351)  │    │ (Webhook)       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### 2. Phone Number Lookup
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Phone Number  │───▶│  Normalize      │───▶│  Airtable       │
│  +19784910236   │    │  Phone Format   │    │  People Table   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### 3. Intent Classification
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   SMS Message   │───▶│  OpenAI LLM     │───▶│  Intent + Data   │
│   "change..."   │    │  Classification │    │  Extraction     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Different Message Types & Processing

### 🎂 Birthday Update Messages
```
Input: "change david kobrosky's birthday to 3/14/1999"
       ↓
Intent: update_person_info
Confidence: 0.95
Extracted: {"birthday": "3/14/1999"}
       ↓
Normalize: "3/14/1999" → "1999-03-14"
       ↓
Update: Airtable People Table
       ↓
Response: "✅ Updated Birthday in your profile"
```

### 🏷️ Tag Management Messages
```
Input: "add tag 'mentor' to david"
       ↓
Intent: manage_tags
Confidence: 0.85
Extracted: {"tags_to_add": ["mentor"]}
       ↓
Update: Airtable People Table (Tags field)
       ↓
Response: "✅ Tags updated - Added: mentor"
```

### 📝 Note Creation Messages
```
Input: "note: david mentioned he's interested in PM role"
       ↓
Intent: create_note
Confidence: 0.90
Extracted: {"note_content": "david mentioned he's interested in PM role"}
       ↓
Create: Airtable Notes Table
       ↓
Response: "✅ Note added: david mentioned he's interested in PM role"
```

### 🔔 Reminder Messages
```
Input: "remind me to reach out to david next month"
       ↓
Intent: create_reminder
Confidence: 0.80
Extracted: {"reminder_action": "reach out to david", "timeline": "next month"}
       ↓
Create: Airtable Reminders Table
       ↓
Response: "✅ Reminder created: reach out to david (due: next month)"
```

### ✅ Confirmation Messages
```
Input: "yes" or "no change"
       ↓
Intent: confirm_changes or no_change
Confidence: 0.95
       ↓
Update: Check-in Status to "Completed"
       ↓
Response: "👍 Thanks for confirming! No changes needed."
```

### 🛑 Opt-out Messages
```
Input: "stop"
       ↓
Intent: opt_out
Confidence: 0.95
       ↓
Update: Person record (Opt-out: True)
       ↓
Response: "You have been unsubscribed from monthly check-ins."
```

## Database Tables Used

### Core People Table (Base: appCA6OJqDxLdiEqf)
- **Table ID:** tbl2pDRalUQpzEBkQ
- **Fields:** Name, Phone, Birthday, Company, Role, Tags, etc.
- **Used for:** Person lookups, profile updates, birthday changes

### SMS Check-ins Table (Base: apptiPfA1VJX5fEZ2)
- **Table ID:** tblyh3CA81E0lilm1
- **Fields:** Person, Month, Status, Transcript, Messages
- **Used for:** Check-in records, message logging, conversation history

### Additional Tables
- **Reminders Table:** For reminder creation
- **Notes Table:** For note storage
- **Followups Table:** For follow-up scheduling

## Error Handling

### Low Confidence (< 0.6)
```
Input: "something unclear"
       ↓
Intent: unclear
Confidence: 0.3
       ↓
Response: "I'm not sure I understood your message. Could you please rephrase?"
```

### Unknown Phone Number
```
Input: SMS from unknown number
       ↓
Lookup: No person found
       ↓
Response: "Unknown phone number" (no response sent)
```

### Processing Error
```
Input: Any message
       ↓
Error: System error occurs
       ↓
Response: "I received your message but had trouble processing it. Please try again."
```

## Complete Flow Example

```
1. 📱 User sends: "change david kobrosky's birthday to 3/14/1999"
2. 📞 Twilio receives SMS and sends webhook to Render
3. 🔍 System looks up phone number in Airtable People table
4. 🧠 OpenAI classifies intent as "update_person_info"
5. 📊 System extracts birthday "3/14/1999"
6. 🔄 Birthday normalized to "1999-03-14"
7. 💾 Airtable People table updated with new birthday
8. 📝 Check-in record created/updated in SMS Check-ins table
9. 📱 Confirmation SMS sent back to user
10. ✅ User receives: "✅ Updated Birthday in your profile"
```

## Admin Commands

### Admin Phone Numbers
- Special phone numbers that can send admin commands
- Bypass normal person lookup
- Access to admin functions

### Admin Commands
- `help` - Show available admin commands
- `add_birthday [name] [date]` - Add birthday for person
- `change_role [name] [role]` - Change person's role
- `change_company [name] [company]` - Change person's company

## Web Interface

### Admin Dashboard
- **URL:** https://kobro-admin.onrender.com/admin
- **Features:** Search people, add birthdays, change roles/companies
- **Access:** Web browser interface for manual updates

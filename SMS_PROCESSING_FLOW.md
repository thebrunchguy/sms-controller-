# SMS Processing Flow Diagram

## System Overview

```
📱 User Phone (9784910236) 
    ↓ SMS Message
📞 Twilio Number (+16469177351)
    ↓ Webhook
🌐 Render App (kobro-admin.onrender.com)
    ↓ Processing
🗄️ Airtable Databases (Cross-Base Integration)
    ↓ Response
📱 User Phone (Confirmation)
```

## Architecture Components

### 🚀 **Production Environment**
- **Render App**: `https://kobro-admin.onrender.com`
- **Twilio Webhook**: `https://kobro-admin.onrender.com/twilio/inbound`
- **Admin Debug**: `https://kobro-admin.onrender.com/admin/debug`

### 🗄️ **Database Architecture (Multi-Base)**
- **Main People Base**: `appCA6OJqDxLdiEqf` (Core People Table)
- **Check-ins Base**: `apptiPfA1VJX5fEZ2` (SMS Processing & Check-ins)
- **Cross-Base Integration**: Seamless data flow between bases

## Message Processing Flow

### 1. SMS Reception
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   User Phone    │───▶│  Twilio Number  │───▶│   Render App    │
│  (9784910236)   │    │ (+16469177351)  │    │ (Webhook)       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### 2. Phone Number Lookup (Cross-Base)
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Phone Number  │───▶│  Normalize      │───▶│  Check-ins      │
│  +19784910236   │    │  Phone Format   │    │  People Table   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │  Fallback to    │
                       │  Main People    │
                       │  Table          │
                       └─────────────────┘
```

### 3. Check-in Record Creation
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Person Found  │───▶│  Create/Update  │───▶│  Check-ins      │
│   (Check-ins)   │    │  Check-in       │    │  Table          │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### 4. Intent Classification
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   SMS Message   │───▶│  OpenAI LLM     │───▶│  Intent + Data   │
│   "change..."   │    │  Classification │    │  Extraction     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### 5. Cross-Base Data Update
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Intent Data   │───▶│  Find Person    │───▶│  Update Main    │
│   (Birthday)    │    │  in Main Table  │    │  People Table   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Different Message Types & Processing

### 🎂 Birthday Update Messages
```
Input: "change david kobrosky's birthday to 3/14/1999"
       ↓
1. Phone Lookup: Find in Check-ins People Table (preferred)
2. Check-in: Create/update check-in record
3. Intent: update_person_info (Confidence: 0.95)
4. Extract: {"birthday": "3/14/1999"}
       ↓
5. Normalize: "3/14/1999" → "1999-03-14"
6. Cross-Base: Find person in Main People Table by name/email
7. Update: Main People Table (Birthday field)
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

### 🏢 **Main People Base** (`appCA6OJqDxLdiEqf`)
- **Core People Table:** `tbl2pDRalUQpzEBkQ`
- **Fields:** Name, Phone, Birthday, Company, Role, Tags, Email, etc.
- **Used for:** Final data storage, profile updates, birthday changes
- **Access:** Read/Write for data updates

### 📱 **Check-ins Base** (`apptiPfA1VJX5fEZ2`)
- **SMS Main View Table:** `tblyh3CA81E0lilm1` (People lookup)
- **Check-ins Table:** `tblivVAPP95ccK8xL` (Check-in records)
- **Messages Table:** `tblivVAPP95ccK8xL` (Message logging)
- **Used for:** SMS processing, check-in records, message history
- **Access:** Primary lookup for SMS processing

### 🔄 **Cross-Base Integration**
- **Phone Lookup:** Check-ins People Table (preferred) → Main People Table (fallback)
- **Data Updates:** Check-ins base finds person → Main base updates data
- **Record Linking:** Person records linked between bases via name/email matching

### 📊 **Additional Tables** (Future)
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
3. 🔍 System normalizes phone number and looks up in Check-ins People table
4. 📝 Check-in record created/updated in Check-ins table
5. 🧠 OpenAI classifies intent as "update_person_info" (confidence: 0.95)
6. 📊 System extracts birthday "3/14/1999" from message
7. 🔄 Birthday normalized to "1999-03-14" format
8. 🔗 Cross-base lookup: Find person in Main People table by name/email
9. 💾 Main People table updated with new birthday
10. 📱 Confirmation SMS sent back to user
11. ✅ User receives: "✅ Updated Birthday in your profile"
```

## Key Technical Improvements

### 🔧 **Phone Number Normalization**
- Handles various formats: `+19784910236`, `9784910236`, `(978) 491-0236`
- Consistent lookup across both Airtable bases
- Fallback mechanism for different table structures

### 🏗️ **Cross-Base Architecture**
- **Primary Lookup:** Check-ins People Table (SMS Main View)
- **Data Storage:** Main People Table (Core data)
- **Seamless Integration:** Automatic record matching between bases

### 🛡️ **Error Handling & Validation**
- **Unknown Phone Numbers:** Graceful rejection with no response
- **Low Confidence Intent:** Clarification requests
- **Processing Errors:** Fallback error messages
- **Admin Commands:** Special processing for admin numbers

### ⚡ **Performance Optimizations**
- **Prefer Check-ins Table:** Faster SMS processing
- **Efficient Lookups:** Normalized phone number matching
- **Minimal API Calls:** Optimized Airtable requests

## Admin Commands

### 🔐 **Admin Phone Numbers**
- **David's Number:** `+19784910236` (also accepts `9784910236`)
- **Bypass:** Normal SMS processing for admin commands
- **Priority:** Admin commands processed before regular SMS

### 📋 **Admin Commands**
- `help` - Show available admin commands
- `controls` - Show available admin commands (same as help)
- `new_friend [name]` - Add new friend to Airtable
- `add_birthday [name] [date]` - Add birthday for person
- `add_email [name] [email]` - Add email for person
- `add_phone [name] [phone]` - Add phone for person
- `add_linkedin [name] [linkedin]` - Add LinkedIn URL for person
- `change_role [name] [role]` - Change person's role  
- `change_company [name] [company]` - Change person's company

### 🔄 **Admin vs Regular SMS**
```
Admin Number (+19784910236):
├── "help" → Admin help message
├── "controls" → Admin help message (same as help)
├── "new friend Sarah Johnson" → Admin command
├── "add_birthday John 1990-01-01" → Admin command
├── "add_email John john@example.com" → Admin command
├── "add_phone John +1234567890" → Admin command
├── "add_linkedin John https://linkedin.com/in/john" → Admin command
└── "change my birthday to 1/1/1990" → Regular SMS processing

Regular Number:
└── "change my birthday to 1/1/1990" → Regular SMS processing
```

## Web Interface

### 🌐 **Admin Dashboard**
- **URL:** https://kobro-admin.onrender.com/admin
- **Features:** Search people, add birthdays, change roles/companies
- **Access:** Web browser interface for manual updates

### 🔍 **Debug Endpoint**
- **URL:** https://kobro-admin.onrender.com/admin/debug
- **Features:** View configuration, check Airtable connections, see sample data
- **Usage:** Troubleshooting and system monitoring

## Production Status

### ✅ **Deployed Features**
- **Open-ended SMS processing** with AI intent classification
- **Cross-base Airtable integration** between people and check-ins
- **Phone number normalization** for consistent lookups
- **Admin command processing** for privileged users
- **Error handling** and validation
- **Production deployment** on Render

### 🧪 **Test Coverage**
- **Comprehensive test suite** in `/tests/` directory
- **Local testing** for development and debugging
- **Production testing** via Twilio webhook
- **Error scenario testing** for robust error handling

### 🚀 **Ready for Production Use**
The system is fully deployed and ready to handle real-world SMS interactions with natural language processing, cross-base data management, and robust error handling.

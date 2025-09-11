# Airtable Schema Requirements for Intent-Based Routing

## Required Tables

### 1. People Table (Existing - Enhanced)
- Name (text)
- Phone (text, E.164)
- Company (text)
- Role (text)
- City (text)
- Tags (multi-select)
- Birthday (date) - **NEW**
- Email (text) - **NEW**
- Last Confirmed (date)
- Check-in Frequency (single select: Monthly / Quarterly)
- Consent (checkbox)
- Opt-out (checkbox)

### 2. Reminders Table (NEW)
- Person (link to People)
- Action (text) - "reach out to this person"
- Timeline (text) - "in a few months"
- Due Date (date) - calculated from timeline
- Priority (single select: Low / Medium / High)
- Status (single select: Pending / Completed / Cancelled)
- Created At (datetime)
- Created By (text) - "SMS" or "Admin"
- Completed At (datetime)

### 3. Notes Table (NEW)
- Person (link to People)
- Content (long text)
- Type (single select: SMS Note / Admin Note / Meeting Note)
- Created At (datetime)
- Created By (text)

### 4. Followups Table (NEW)
- Person (link to People)
- Reason (text) - why the follow-up is needed
- Timeline (text) - "next month"
- Scheduled Date (date) - calculated from timeline
- Status (single select: Scheduled / Completed / Cancelled)
- Created At (datetime)
- Created By (text)
- Completed At (datetime)

## Environment Variables Required

Add these to your `.env` file:

```bash
# Existing variables
AIRTABLE_API_KEY=your_api_key
AIRTABLE_BASE_ID=your_base_id
AIRTABLE_PEOPLE_TABLE=People
AIRTABLE_CHECKINS_TABLE=Check-ins
AIRTABLE_MESSAGES_TABLE=Messages

# New table names (you can customize these)
AIRTABLE_REMINDERS_TABLE=Reminders
AIRTABLE_NOTES_TABLE=Notes
AIRTABLE_FOLLOWUPS_TABLE=Followups
```

## Intent Mapping

| Intent | Target Table | Example Message |
|--------|-------------|-----------------|
| update_person_info | People | "update david's birthday to 03/14/1999" |
| manage_tags | People | "tag david with mentor" |
| create_reminder | Reminders | "remind me to reach out in a few months" |
| create_note | Notes | "note: david mentioned he's looking for a new job" |
| schedule_followup | Followups | "schedule a follow-up next month" |
| no_change | None | "no change" |
| confirm_changes | None | "yes" |
| opt_out | People | "stop" |
| unclear | None | ambiguous messages |

## Usage Examples

### Birthday Update
**Message**: "hey, can you update david kobrosky's birthday to be 03/14/1999?"
- Intent: `update_person_info`
- Target: People table
- Action: Update Birthday field

### Tag Management
**Message**: "Hey can you tag David with tag 'mentor'"
- Intent: `manage_tags`
- Target: People table (Tags field)
- Action: Add "mentor" to Tags array

### Reminder Creation
**Message**: "can you remind me to reach out to this person in a few months?"
- Intent: `create_reminder`
- Target: Reminders table
- Action: Create new reminder record with due date ~60 days from now

### Note Taking
**Message**: "note: david mentioned he's interested in the PM role"
- Intent: `create_note`
- Target: Notes table
- Action: Create new note record

### Follow-up Scheduling
**Message**: "schedule a follow-up next month to discuss the project"
- Intent: `schedule_followup`
- Target: Followups table
- Action: Create new follow-up record

## Setup Instructions

1. **Create the new Airtable tables** with the fields listed above
2. **Update your `.env` file** with the new table names
3. **Test the system** with sample messages
4. **Customize the intent classification** by modifying the prompts in `intent_classifier.py`

## Benefits

- **Multiple data types**: Different types of information go to appropriate tables
- **Natural language**: Users can express intents in various ways
- **Scalable**: Easy to add new intents and tables
- **Organized**: Clear separation of concerns between different data types
- **Flexible**: Can handle complex multi-step workflows 
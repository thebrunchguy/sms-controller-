# Technical Spec: Monthly SMS Airtable Check-ins (LLM + MCP Option)

## Scope
```
- Monthly SMS check-ins to keep an Airtable “People” table up to date.
- Users can reply “no change” or free-text updates.
- Bot proposes a change set; on “YES” it writes to Airtable.
- Every message logged for review.
- Outbound SMS should include a bulleted snapshot of current Airtable data.
- Optional MCP server so LLM can call Airtable/Twilio tools directly.
```

## Tech Stack
```
- Backend: FastAPI (Python)
- Database: Airtable (People, Check-ins, Messages tables)
- Messaging: Twilio (Messaging Service SID)
- Scheduler: Cron or POST endpoint (triggered by job runner)
- Deployment: Docker + Render/Fly/Heroku
- LLM: OpenAI (with JSON schema tool call)
- Optional: MCP server to expose Airtable and Twilio operations
```

## Airtable Schema
```
**People**
- Name (text)
- Phone (text, E.164)
- Company (text)
- Role (text)
- City (text)
- Tags (multi-select)
- Last Confirmed (date)
- Check-in Frequency (single select: Monthly / Quarterly)
- Consent (checkbox)
- Opt-out (checkbox)

**Check-ins**
- Person (link to People)
- Month (text, YYYY-MM)
- Status (single select: Sent / In progress / Completed / Failed / Opted-out)
- Pending Changes (long text JSON)
- Transcript (long text)
- Message SID (text)
- Last Message At (datetime)

**Messages**
- Check-in (link to Check-ins)
- When (datetime)
- Direction (Inbound / Outbound / System)
- From (text)
- Body (long text)
- Twilio SID (text)
- Parsed JSON (long text)
```

## Outbound SMS Template
```
Hi {Name}! Monthly check-in. Here’s what I have:
• Company: {Company|—}
• Role: {Role|—}
• City: {City|—}
• Tags: {tag1, tag2|—}
Anything changed since {LastConfirmed|“last month”}?
Reply with updates or “No change”. Reply STOP to opt out.
```
- If message exceeds ~420 chars, either split into two messages or support `MORE` keyword.
- Keep values truncated to ~40 chars for readability.

## LLM Schema
```json
{
  "type": "object",
  "properties": {
    "no_change": {"type":"boolean"},
    "company": {"type":"string"},
    "role": {"type":"string"},
    "city": {"type":"string"},
    "tags_add": {"type":"array","items":{"type":"string"}},
    "tags_remove": {"type":"array","items":{"type":"string"}},
    "confirmation_text": {"type":"string"},
    "confidence": {"type":"number","minimum":0,"maximum":1}
  }
}
```
- Model always returns a `confirmation_text` summarizing changes.
- Writes to Airtable happen only after explicit **YES** confirmation.

## Endpoints
```
POST /jobs/send-monthly
- Sweep People who are due (based on Last Confirmed + Frequency).
- Skip if Opt-out or no Consent.
- Upsert Check-in for Person+Month with Status=Sent.
- Compose snapshot, send SMS via Twilio, log Outbound Message.

POST /twilio/inbound
- Match Person by phone, upsert Check-in (Status=In progress).
- Log Inbound Message.
- Branch:
  - "no change" → update Last Confirmed, mark Completed, reply 👍
  - "YES" → apply Pending Changes, update Person, mark Completed, reply ✅
  - Else → call LLM with snapshot + inbound text → get structured intent + confirmation_text
    - Save as Pending Changes
    - Reply with confirmation_text

POST /twilio/status
- Log delivery events as System Messages for audit.
```

## MCP Tools (Optional)
```
- airtable.people.get_by_phone
- airtable.people.update_fields
- airtable.checkins.log_message
- sms.send
```
- When `USE_MCP=true`, FastAPI app routes calls through MCP.
- When `USE_MCP=false`, use local Airtable/Twilio adapters.

## Extensibility
```
- Add richer tag taxonomy (e.g., “Remote only”, “Open to advising”).
- Normalize company/role/city strings via post-processing or LLM.
- Confidence threshold: if <0.6, reply with clarifying question instead of summary.
- Optional: web review link for long or ambiguous updates.
- Feature flags:
  - USE_MCP (on/off)
  - USE_OPENAI (on/off)
  - SEND_LINK_ON_COMPLEX (on/off)
```

## Acceptance Criteria
```
- Outbound SMS always includes snapshot of current fields.
- Free-text replies parsed via LLM, summary sent back.
- No writes until user replies YES.
- "No change" updates Last Confirmed and closes Check-in.
- "YES" applies Pending Changes to People and closes Check-in.
- STOP respected → Opt-out=true, no further messages.
- Every message (Inbound, Outbound, System) logged in Messages.
- Delivery status written to Messages from Twilio status callbacks.
```

## Control Flow Summary
```
1. Scheduler sends monthly SMS with snapshot → Check-in row created (Status=Sent).
2. User replies:
   - "No change" → mark Completed.
   - "YES" → apply Pending Changes → mark Completed.
   - Free text → LLM extracts updates → system replies with confirmation → store Pending Changes.
3. User confirms → updates applied → Last Confirmed updated.
4. All interactions logged in Messages and appended to Check-in Transcript.
```

## Minimal Test Cases
```
1. Reply "no change" → Last Confirmed updated, Check-in Completed.
2. Reply "left Etsy, now at Figma as PM in NYC; also job hunting"
   → LLM proposes updates, sends confirmation.
   → Reply YES → Airtable updated accordingly.
3. Ambiguous reply → low confidence → bot asks clarifying question.
4. Reply STOP → Opt-out set, future jobs skip this Person.
5. Delivery status logged in Messages.
```

---

### Quick start
1) Fill `.env` from `.env.example`  
2) `pip install -r requirements.txt`  
3) `uvicorn app.main:app --reload`  
4) Point Twilio webhook to `POST {APP_BASE_URL}/twilio/inbound`  
5) Trigger `POST {APP_BASE_URL}/jobs/send-monthly` to test outbound

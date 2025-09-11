# SMS Check-in Application Setup Guide

This guide explains how to get the SMS Check-in Application running from scratch.

## Prerequisites

- Python 3.11+
- Git
- Airtable account with API access
- Twilio account
- OpenAI API key
- Render account (for production deployment)

## Environment Setup

### 1. Clone the Repository
```bash
git clone <repository-url>
cd "People Data Updates"
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Environment Variables

Create a `config/config.env` file with the following variables:

```env
# Airtable Configuration
AIRTABLE_API_KEY=your_airtable_api_key_here
AIRTABLE_BASE_ID=your_airtable_base_id_here
AIRTABLE_PEOPLE_TABLE=your_table_id_here
AIRTABLE_CHECKINS_TABLE=your_checkins_table_id_here
AIRTABLE_MESSAGES_TABLE=your_messages_table_id_here

# Twilio Configuration
TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_PHONE_NUMBER=your_twilio_phone_number

# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-4o-mini

# Application Configuration
APP_BASE_URL=http://localhost:8000
APP_ENV=development
```

## Airtable Setup

### Finding the Correct Table IDs

1. **Base ID**: Found in your Airtable URL: `https://airtable.com/app[BASE_ID]/tbl[TABLE_ID]/viw[VIEW_ID]`
2. **Table ID**: Use the actual table ID (starts with `tbl`), NOT the view name
3. **View Names vs Table IDs**: 
   - ❌ Don't use: "Grid view", "Core Network Main View" (these are view names)
   - ✅ Use: `tbl2pDRalUQpzEBkQ` (this is the table ID)

### Example Airtable URL Breakdown
```
https://airtable.com/appCA6OJqDxLdiEqf/tbl2pDRalUQpzEBkQ/viw1hJQyx4GOtEOEp
                                    ^^^^^^^^^^^^^^^^^ ^^^^^^^^^^^^^^^^^
                                    BASE_ID           TABLE_ID
```

## Running Locally

### Start the Application
```bash
python3 run.py
```

The application will start on `http://localhost:8000`

### Access Points
- **Main App**: `http://localhost:8000`
- **Admin Dashboard**: `http://localhost:8000/admin`
- **API Documentation**: `http://localhost:8000/docs`
- **Debug Endpoint**: `http://localhost:8000/admin/debug`

## Production Deployment (Render)

### 1. Connect Repository
- Connect your GitHub repository to Render
- Set up automatic deployments from the `main` branch

### 2. Environment Variables in Render
Set the same environment variables in Render dashboard:
- Go to your service → Environment tab
- Add all the variables from `config/config.env`
- **IMPORTANT**: Use table IDs, not view names

### 3. Build Settings
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `python3 run.py`

## Common Issues & Solutions

### 1. Import Errors
**Error**: `ModuleNotFoundError: No module named 'intent_classifier'`

**Solution**: Ensure all imports in `main.py` and `intent_handlers.py` use relative imports:
```python
# Correct
from . import airtable, twilio_utils

# Incorrect
import airtable
import twilio_utils
```

### 2. Search Not Working
**Error**: Search returns no results

**Solution**: Check that you're using table IDs, not view names:
- ❌ Wrong: `AIRTABLE_PEOPLE_TABLE=Core Network Main View`
- ✅ Correct: `AIRTABLE_PEOPLE_TABLE=tbl2pDRalUQpzEBkQ`

### 3. Deployment Failures
**Error**: Deployment fails with import errors

**Solution**: 
1. Fix import errors locally first
2. Test with `python3 run.py`
3. Commit and push changes
4. Wait for deployment to complete

### 4. Port Already in Use
**Error**: `[Errno 48] Address already in use`

**Solution**: Kill the process using port 8000:
```bash
lsof -ti:8000 | xargs kill -9
```

## Testing the Application

### 1. Test Search Functionality
```bash
curl "https://admin.kobro.co/admin/search?query=david"
```

### 2. Test Debug Endpoint
```bash
curl "https://admin.kobro.co/admin/debug"
```

Expected response should show:
- Correct table name (table ID, not view name)
- Non-zero total_records
- Sample records with actual data

### 3. Test Admin Dashboard
Visit `https://admin.kobro.co/admin` and verify:
- Page loads successfully
- Pointing finger emoji favicon appears 👉
- Search box works and returns results

## File Structure

```
People Data Updates/
├── app/
│   ├── main.py              # FastAPI application
│   ├── airtable.py          # Airtable integration
│   ├── twilio_utils.py      # Twilio SMS functionality
│   ├── llm.py              # OpenAI integration
│   ├── scheduler.py         # Job scheduling
│   ├── admin_sms.py         # Admin SMS commands
│   ├── intent_classifier.py # Intent classification
│   └── intent_handlers.py   # Intent handling
├── config/
│   └── config.env           # Environment variables
├── requirements.txt         # Python dependencies
├── run.py                  # Application entry point
└── SETUP_GUIDE.md          # This file
```

## Key Features

- **Admin Dashboard**: Web interface for managing people data
- **Search Functionality**: Search people by name
- **SMS Integration**: Send and receive SMS via Twilio
- **Airtable Integration**: Sync data with Airtable
- **AI Processing**: Use OpenAI for intent classification
- **Favicon**: Pointing finger emoji 👉 in browser tab

## Maintenance

### Updating Dependencies
```bash
pip install --upgrade -r requirements.txt
```

### Viewing Logs (Render)
- Go to Render dashboard
- Select your service
- Click "Logs" tab

### Backup Configuration
Always backup your `config/config.env` file before making changes.

## Support

If you encounter issues:
1. Check the debug endpoint: `/admin/debug`
2. Verify environment variables are correct
3. Ensure table IDs are used (not view names)
4. Check Render deployment logs
5. Test locally first before deploying

---

**Last Updated**: September 11, 2025
**Version**: 1.0

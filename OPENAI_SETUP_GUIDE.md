# OpenAI Setup Guide

## Current Status
✅ OpenAI API key is configured and working  
✅ Model is set to `gpt-4o-mini`  
❌ Intent classifier may not be loading environment variables properly

## Configuration Files

### 1. Environment Variables (`config/config.env`)
```bash
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o-mini
```

### 2. Intent Classifier Loading
The intent classifier should load environment variables at startup. Check that `app/intent_classifier.py` has:

```python
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('config/config.env')

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
```

## Troubleshooting Steps

### 1. Verify API Key is Valid
```bash
cd "/Users/davidkobrosky/Downloads/People Data Updates"
python3 -c "
import os
from dotenv import load_dotenv
load_dotenv('config/config.env')
print('API Key:', os.getenv('OPENAI_API_KEY')[:20] + '...')
"
```

### 2. Test OpenAI API Directly
```bash
python3 -c "
import os
from dotenv import load_dotenv
load_dotenv('config/config.env')
from openai import OpenAI

client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
response = client.chat.completions.create(
    model='gpt-4o-mini',
    messages=[{'role': 'user', 'content': 'Test message'}],
    max_tokens=10
)
print('Success:', response.choices[0].message.content)
"
```

### 3. Check Intent Classifier
```bash
python3 -c "
import sys
sys.path.append('app')
from intent_classifier import classify_intent

result = classify_intent('remind me to call david', {})
print('Intent:', result.get('intent'))
print('Confidence:', result.get('confidence'))
"
```

## Common Issues & Solutions

### Issue 1: "OpenAI API key not configured"
**Cause:** Environment variables not loaded properly  
**Solution:** Ensure `load_dotenv('config/config.env')` is called before using OpenAI

### Issue 2: "Invalid API key"
**Cause:** API key is expired or invalid  
**Solution:** Generate a new API key from https://platform.openai.com/api-keys

### Issue 3: "Rate limit exceeded"
**Cause:** Too many requests  
**Solution:** Wait a few minutes or upgrade your OpenAI plan

### Issue 4: "Model not found"
**Cause:** Model name is incorrect  
**Solution:** Use `gpt-4o-mini`, `gpt-4`, or `gpt-3.5-turbo`

## Production Deployment

### For Render.com
1. Add environment variables in Render dashboard
2. Set `OPENAI_API_KEY` and `OPENAI_MODEL`
3. Restart the service

### For Local Development
1. Ensure `.env` file is in project root
2. Run `source .env` or use `python-dotenv`
3. Test with the commands above

## Monitoring

### Check API Usage
Visit https://platform.openai.com/usage to monitor:
- API calls per day
- Token usage
- Costs
- Rate limits

### Logs
Check application logs for:
- "OpenAI API key not configured" errors
- Rate limit warnings
- Model errors

## Best Practices

1. **Never commit API keys** to version control
2. **Use environment variables** for all sensitive data
3. **Test API connectivity** before deployment
4. **Monitor usage** to avoid unexpected costs
5. **Use fallback logic** when API is unavailable (like the timeline extractor)

## Fallback System

The system now has a robust fallback:
- If OpenAI fails → Uses keyword-based classification
- If timeline extraction fails → Uses comprehensive regex patterns
- If person lookup fails → Still creates reminder with available data

This ensures reminders work even when OpenAI is unavailable.

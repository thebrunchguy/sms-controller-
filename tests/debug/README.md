# Debug and Diagnostic Tests

This directory contains debug and diagnostic tests for troubleshooting issues.

## Test Files

- `debug_checkin_creation.py` - Debug check-in record creation
- `debug_checkins_people_lookup.py` - Debug people lookup in check-ins
- `debug_env.py` - Debug environment variable loading
- `debug_full_sms_flow.py` - Debug complete SMS processing flow
- `debug_intent_handler.py` - Debug intent handling
- `debug_phone_lookup.py` - Debug phone number lookup

## Running Debug Tests

```bash
cd tests/debug
python debug_env.py
python debug_phone_lookup.py
python debug_full_sms_flow.py
```

## Purpose

These tests help diagnose issues when:
- Check-ins aren't being created properly
- Phone number lookups are failing
- Environment variables aren't loading
- SMS processing has errors
- Intent handling isn't working

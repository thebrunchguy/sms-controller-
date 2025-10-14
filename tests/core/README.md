# Core Functionality Tests

This directory contains tests for the core functionality of the People Data Updates system.

## Test Files

- `test_airtable.py` - Tests basic Airtable connectivity and functions
- `test_admin_sms.py` - Tests admin SMS command processing
- `test_intent_system.py` - Tests intent classification system
- `test_sms.py` - Tests SMS processing workflow
- `test_simple_sms.py` - Basic SMS functionality tests
- `test_birthday_update_sms.py` - Tests birthday update via SMS
- `test_sms_debug.py` - Debug SMS processing

## Running Core Tests

```bash
cd tests/core
python test_airtable.py
python test_admin_sms.py
python test_intent_system.py
```

## Purpose

These tests verify that the main application features work correctly:
- Airtable integration
- SMS processing
- Intent classification
- Admin commands
- Data updates

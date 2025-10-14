# Status and Validation Tests

This directory contains tests for checking system status and validating configurations.

## Test Files

- `check_final_status.py` - Check final application status
- `check_new_number.py` - Check new phone number handling
- `check_twilio_status.py` - Check Twilio service status
- `phone_number_test.py` - Test phone number formatting

## Running Status Tests

```bash
cd tests/status
python check_twilio_status.py
python check_final_status.py
python phone_number_test.py
```

## Purpose

These tests verify:
- Application is running correctly
- Twilio service is accessible
- Phone number formatting works
- New phone numbers are handled properly
- System configuration is valid

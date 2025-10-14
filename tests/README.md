# Test Suite

This folder contains all the test files for the People Data Updates SMS check-in application.

## Test Categories

### 🧪 Core Functionality Tests
- **`test_airtable.py`** - Tests basic Airtable connectivity and functions
- **`test_admin_sms.py`** - Tests admin SMS command processing
- **`test_intent_system.py`** - Tests intent classification system
- **`test_sms.py`** - Tests SMS processing workflow
- **`test_simple_sms.py`** - Basic SMS functionality tests

### 🔍 Debug and Diagnostic Tests
- **`debug_checkin_creation.py`** - Debug check-in record creation
- **`debug_checkins_people_lookup.py`** - Debug people lookup in check-ins
- **`debug_env.py`** - Debug environment variable loading
- **`debug_full_sms_flow.py`** - Debug complete SMS processing flow
- **`debug_intent_handler.py`** - Debug intent handling
- **`debug_phone_lookup.py`** - Debug phone number lookup

### 📊 Data Exploration Tests
- **`explore_airtable.py`** - Explores base structure and metadata
- **`simple_airtable_test.py`** - Basic connectivity tests
- **`detailed_table_test.py`** - Detailed record structure examination
- **`simple_table_test.py`** - Tests direct table access without filters

### ✅ Status and Validation Tests
- **`check_final_status.py`** - Check final application status
- **`check_new_number.py`** - Check new phone number handling
- **`check_twilio_status.py`** - Check Twilio service status
- **`phone_number_test.py`** - Test phone number formatting

### 🚀 Integration Tests
- **`test_birthday_update_sms.py`** - Test birthday update via SMS
- **`test_sms_debug.py`** - Debug SMS processing
- **`single_test_sms.py`** - Single SMS test
- **`test.py`** - General test file

### 🏃 Test Runner
- **`run_tests.py`** - Test runner script to execute all tests

## Running Tests

### Run All Tests
```bash
cd tests
python3 run_tests.py
```

### Run Tests by Category
```bash
# Core functionality tests
cd tests/core
python3 test_airtable.py

# Debug tests
cd tests/debug
python3 debug_env.py

# Status validation tests
cd tests/status
python3 check_twilio_status.py

# Data exploration tests
cd tests/exploration
python3 explore_airtable.py

# Integration tests
cd tests/integration
python3 single_test_sms.py
```

### Run from Project Root
```bash
python3 tests/run_tests.py
```

## Test Configuration

Tests use the configuration from `../config/config.env`. Make sure this file contains your:
- Airtable Personal Access Token
- Base ID
- Table names

## Test Results

- ✅ **Success**: Test passed without errors
- ❌ **Failure**: Test encountered an error
- 🔍 **Info**: Test is gathering information

## Adding New Tests

1. Create your test file in this folder
2. Add it to the `tests` list in `run_tests.py`
3. Follow the naming convention: `test_*.py` or `*_test.py` 
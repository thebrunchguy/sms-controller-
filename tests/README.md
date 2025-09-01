# Test Suite

This folder contains all the test files for the Monthly SMS Check-in application.

## Test Files

### Core Tests
- **`test_airtable.py`** - Tests basic Airtable connectivity and functions
- **`simple_table_test.py`** - Tests direct table access without filters
- **`run_tests.py`** - Test runner script to execute all tests

### Utility Tests
- **`explore_airtable.py`** - Explores base structure and metadata
- **`simple_airtable_test.py`** - Basic connectivity tests
- **`detailed_table_test.py`** - Detailed record structure examination

## Running Tests

### Run All Tests
```bash
cd tests
python3 run_tests.py
```

### Run Individual Tests
```bash
cd tests
python3 test_airtable.py
python3 simple_table_test.py
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
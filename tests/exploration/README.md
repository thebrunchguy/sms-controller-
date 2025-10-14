# Data Exploration Tests

This directory contains tests for exploring and understanding Airtable data structures.

## Test Files

- `explore_airtable.py` - Explores base structure and metadata
- `simple_airtable_test.py` - Basic connectivity tests
- `detailed_table_test.py` - Detailed record structure examination
- `simple_table_test.py` - Tests direct table access without filters

## Running Exploration Tests

```bash
cd tests/exploration
python explore_airtable.py
python detailed_table_test.py
```

## Purpose

These tests help understand:
- Airtable base structure
- Table schemas and field types
- Record formats and data types
- API response structures
- Data relationships between tables

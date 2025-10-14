# Scripts Directory

This directory contains utility scripts and backups for the People Data Updates project.

## Structure

### `utilities/` - Active Scripts
- `run.py` - Application startup script (used by Render deployment)
- `setup_cross_base_references.py` - Sets up Airtable cross-base references for SMS check-ins

### Backup Files
- `main.py.backup` - Backup of main.py from September 1st (outdated)
- `main.py.backup2` - Additional backup from September 1st (outdated)

## Usage

### Running the Application
```bash
python scripts/utilities/run.py
```

### Setting up Cross-Base References
```bash
python scripts/utilities/setup_cross_base_references.py
```

## Notes

- The backup files are outdated and can be removed if not needed
- The `run.py` script is the primary entry point for the application
- The setup script is used for initial Airtable configuration

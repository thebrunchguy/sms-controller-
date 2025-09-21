# Project Structure

This document describes the organized structure of the People Data Updates project.

## 📁 Directory Organization

### Root Directory
- `README.md` - Project documentation
- `requirements.txt` - Python dependencies
- `Dockerfile` - Container configuration
- `render.yaml` - Deployment configuration
- `.env` - Environment variables (not tracked)

### 📱 `app/` - Main Application
Core FastAPI application and business logic:
- `main.py` - FastAPI application entry point
- `admin_sms.py` - Admin SMS command processing (hybrid regex + MCP)
- `airtable.py` - Airtable API integration
- `twilio_utils.py` - Twilio SMS utilities
- `intent_classifier.py` - LLM-based intent classification
- `intent_handlers.py` - Intent handling logic
- `parser.py` - Message parsing utilities
- `compose.py` - Message composition
- `llm.py` - LLM integration
- `scheduler.py` - Task scheduling

### 🤖 `mcp_parser/` - MCP (Multi-Capability Protocol) Package
Natural language command parsing using MCP framework:
- `__init__.py` - Package initialization
- `final_mcp_server.py` - Main MCP server for complex command parsing
- `final_mcp_client.py` - MCP client for server communication
- `mcp_sync_client.py` - Synchronous MCP client (works in async contexts)
- `mcp_tuple_converter.py` - Fix for MCP framework Pydantic validation issues

### 🔄 `keep_alive/` - Keep-Alive Scripts
Scripts to keep the application running:
- `keep_alive.py` - Basic keep-alive script
- `robust_keep_alive.py` - Enhanced keep-alive with error handling
- `simple_keep_alive.py` - Minimal keep-alive script

### 🛠️ `scripts/` - Utility Scripts
- `utilities/run.py` - Application runner
- `utilities/setup_cross_base_references.py` - Database setup script
- `main.py.backup` - Backup of main application
- `main.py.backup2` - Additional backup

### 🧪 `tests/` - Test Suite
Comprehensive test suite for all components:
- `test_admin_sms.py` - Admin SMS command tests
- `test_airtable.py` - Airtable integration tests
- `test_sms.py` - SMS processing tests
- `debug_*.py` - Debug and diagnostic scripts
- `check_*.py` - Status checking scripts
- `run_tests.py` - Test runner

### ⚙️ `config/` - Configuration
Environment configuration files:
- `config.env` - Main configuration
- `config.env.example` - Configuration template
- `config.example.env` - Alternative configuration template

### 📚 `docs/` - Documentation
Project documentation:
- `IMPLEMENTATION_SUMMARY.md` - Implementation overview
- `SCHEMA_REQUIREMENTS.md` - Database schema requirements
- `SETUP_GUIDE.md` - Setup instructions
- `SMS_PROCESSING_FLOW.md` - SMS processing workflow
- `PROJECT_STRUCTURE.md` - This file

## 🔧 Key Features

### Hybrid Command Parsing
- **Regex First**: Fast parsing for structured commands
- **MCP Fallback**: Natural language processing for complex commands
- **Async Safe**: Works within FastAPI async contexts

### MCP Integration
- **Framework Fix**: Custom tuple converter to fix Pydantic validation issues
- **Async Context**: Synchronous client that works in async environments
- **Natural Language**: Advanced pattern matching for human-like commands

### Clean Architecture
- **Separation of Concerns**: Clear separation between components
- **Modular Design**: Easy to maintain and extend
- **Test Coverage**: Comprehensive test suite

## 🚀 Usage

### Running the Application
```bash
# Start the FastAPI server
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Run keep-alive script
python3 keep_alive/robust_keep_alive.py

# Run tests
python3 tests/run_tests.py
```

### MCP Command Parsing
```python
from mcp_parser.mcp_sync_client import test_mcp_sync

# Parse natural language command
result = test_mcp_sync("can you add in a linkedin for bobby housel - here's the url https://linkedin.com/in/bobby")
```

## 📝 Notes

- All import paths have been updated to reflect the new structure
- MCP package renamed to `mcp_parser` to avoid conflicts with global MCP package
- Keep-alive scripts organized for easy deployment
- Test files maintained in original structure for compatibility
- Documentation centralized in `docs/` directory

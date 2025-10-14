# MCP Parser Package

This directory contains the Multi-Capability Protocol (MCP) implementation for advanced natural language command parsing.

## Files

- `__init__.py` - Package initialization
- `final_mcp_server.py` - Main MCP server for complex command parsing
- `final_mcp_client.py` - MCP client for server communication
- `mcp_sync_client.py` - Synchronous MCP client wrapper (used by admin_sms.py)
- `mcp_tuple_converter.py` - Fix for MCP framework Pydantic validation issues

## Usage

The MCP parser is used by the admin SMS system for complex natural language command parsing. It provides fallback parsing when simple regex patterns aren't sufficient.

## Integration

- **Used by**: `app/admin_sms.py` - Admin SMS command processing
- **Purpose**: Advanced natural language understanding for complex admin commands
- **Fallback**: When MCP is unavailable, the system falls back to regex-based parsing

## Dependencies

- MCP framework
- Pydantic (with custom tuple converter for compatibility)
- Async/await support for FastAPI integration

## Status

**Active** - Currently used by the admin SMS system for advanced command parsing.

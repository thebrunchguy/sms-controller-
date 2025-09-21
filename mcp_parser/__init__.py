"""
MCP (Multi-Capability Protocol) package for admin command parsing.

This package contains:
- final_mcp_server.py: The main MCP server for parsing complex admin commands
- final_mcp_client.py: Client for communicating with the MCP server
- mcp_sync_client.py: Synchronous client that works within async contexts
- mcp_tuple_converter.py: Utility to fix MCP framework Pydantic validation issues
"""

from .mcp_sync_client import test_mcp_sync

__all__ = ['test_mcp_sync']

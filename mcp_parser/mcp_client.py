#!/usr/bin/env python3
"""
MCP Client for Admin Command Parsing
Handles communication with the MCP server for complex command parsing
"""

import asyncio
import json
import logging
from typing import Any, Dict, Optional
from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

logger = logging.getLogger(__name__)

async def parse_admin_command_sync(message: str, conversation_id: Optional[str] = None) -> Dict[str, Any]:
    """Parse a single admin command using MCP server"""
    server_params = StdioServerParameters(
        command="python3",
        args=["mcp_server.py"]
    )
    
    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                
                result = await session.call_tool(
                    "parse_admin_command",
                    {
                        "message": message,
                        "conversation_id": conversation_id
                    }
                )
                
                # Parse the JSON response
                response_text = result.content[0].text
                return json.loads(response_text)
                
    except Exception as e:
        logger.error(f"Error parsing command via MCP: {e}")
        return {
            "error": str(e),
            "command": None,
            "confidence": 0.0
        }

# Test function
async def test_parser():
    """Test the MCP parser with various commands"""
    test_commands = [
        "can you add in a linkedin for bobby housel - here's the url https://linkedin.com/in/bobby",
        "I met Sarah Johnson at the conference",
        "add email john doe john@example.com",
        "bobby housel works at microsoft now",
        "what's bobby's linkedin?",
        "https://linkedin.com/in/bobby-housel"
    ]
    
    for cmd in test_commands:
        print(f"\nCommand: {cmd}")
        result = await parse_admin_command_sync(cmd)
        print(f"Result: {json.dumps(result, indent=2)}")

if __name__ == "__main__":
    asyncio.run(test_parser())

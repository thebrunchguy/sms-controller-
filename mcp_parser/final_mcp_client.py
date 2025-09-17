#!/usr/bin/env python3
"""
Final MCP client - using the most basic pattern
"""

import asyncio
import json
import logging
import sys
import os
from typing import Any, Dict

# Import MCP from the global package, not our local mcp_parser
import importlib.util
import subprocess

# Remove our local mcp_parser from the path temporarily to import global MCP
current_path = sys.path.copy()
if os.path.dirname(os.path.dirname(__file__)) in sys.path:
    sys.path.remove(os.path.dirname(os.path.dirname(__file__)))

# Try to import MCP from the global package
try:
    from mcp.client.session import ClientSession
    from mcp.client.stdio import StdioServerParameters, stdio_client
except ImportError as e:
    # If MCP is not available, we'll handle this gracefully
    print(f"MCP package not available: {e}, falling back to regex-only parsing")
    ClientSession = None
    StdioServerParameters = None
    stdio_client = None
finally:
    # Restore the original path
    sys.path = current_path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_final_mcp(message: str) -> Dict[str, Any]:
    """Test final MCP server"""
    if not ClientSession or not StdioServerParameters or not stdio_client:
        return {
            "error": "MCP package not available",
            "command": None,
            "confidence": 0.0
        }
    
    server_params = StdioServerParameters(
        command="python3",
        args=[os.path.join(os.path.dirname(__file__), "final_mcp_server.py")]
    )

    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                # Initialize session
                init_result = await session.initialize()
                logger.info(f"Initialization result: {init_result}")

                # Call tool
                logger.info("Calling tool...")
                result = await session.call_tool(
                    "parse_admin_command",
                    {
                        "message": message
                    }
                )
                logger.info(f"Tool call result: {result}")

                # Parse the JSON response
                response_text = result.content[0].text
                logger.info(f"Response text: {response_text}")
                return json.loads(response_text)

    except Exception as e:
        logger.error(f"Error parsing command via MCP: {e}")
        return {
            "error": str(e),
            "command": None,
            "confidence": 0.0
        }

async def main():
    """Test the final MCP server"""
    message = "can you add in a linkedin for bobby housel - here's the url https://linkedin.com/in/bobby"
    print(f"Testing message: {message}")
    result = await test_final_mcp(message)
    print(f"Result: {json.dumps(result, indent=2)}")

if __name__ == "__main__":
    asyncio.run(main())

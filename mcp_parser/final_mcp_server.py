#!/usr/bin/env python3
"""
Final MCP server - using the most basic pattern
"""

import asyncio
import json
import logging
from typing import Any, Dict, List
from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import CallToolResult, Tool, TextContent
from mcp.server import NotificationOptions
from mcp_tuple_converter import create_safe_call_tool_result, create_safe_text_content

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create server
server = Server("final-parser")

@server.list_tools()
async def list_tools() -> List[Tool]:
    """List available tools"""
    return [
        Tool(
            name="parse_admin_command",
            description="Parse admin SMS commands",
            inputSchema={
                "type": "object",
                "properties": {
                    "message": {
                        "type": "string",
                        "description": "The admin command message to parse"
                    }
                },
                "required": ["message"]
            }
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> CallToolResult:
    """Handle tool calls"""
    logger.info(f"call_tool called with name={name}, arguments={arguments}")
    
    if name == "parse_admin_command":
        message = arguments.get("message", "")
        logger.info(f"Parsing message: {message}")
        
        # Advanced parsing logic for natural language
        import re
        
        # Pattern matching for different command types
        patterns = {
            "add_linkedin": [
                r"add.*linkedin.*?for\s+(\w+(?:\s+\w+)*).*?(https?://[^\s]+|linkedin\.com/[^\s]+)",
                r"add.*linkedin.*?(\w+(?:\s+\w+)*).*?(https?://[^\s]+|linkedin\.com/[^\s]+)",
                r"linkedin.*?for\s+(\w+(?:\s+\w+)*).*?(https?://[^\s]+|linkedin\.com/[^\s]+)",
                r"linkedin.*?(\w+(?:\s+\w+)*).*?(https?://[^\s]+|linkedin\.com/[^\s]+)",
                r"(\w+(?:\s+\w+)*).*?linkedin.*?(https?://[^\s]+|linkedin\.com/[^\s]+)",
                r"can.*?you.*?add.*?linkedin.*?for\s+(\w+(?:\s+\w+)*).*?(https?://[^\s]+|linkedin\.com/[^\s]+)",
                r"can.*?you.*?add.*?linkedin.*?(\w+(?:\s+\w+)*).*?(https?://[^\s]+|linkedin\.com/[^\s]+)"
            ],
            "add_email": [
                r"add.*email.*?for\s+(\w+(?:\s+\w+)*).*?([^\s]+@[^\s]+\.[^\s]+)",
                r"add.*email.*?(\w+(?:\s+\w+)*).*?([^\s]+@[^\s]+\.[^\s]+)",
                r"email.*?for\s+(\w+(?:\s+\w+)*).*?([^\s]+@[^\s]+\.[^\s]+)",
                r"email.*?(\w+(?:\s+\w+)*).*?([^\s]+@[^\s]+\.[^\s]+)",
                r"(\w+(?:\s+\w+)*).*?email.*?([^\s]+@[^\s]+\.[^\s]+)",
                r"can.*?you.*?add.*?email.*?for\s+(\w+(?:\s+\w+)*).*?([^\s]+@[^\s]+\.[^\s]+)",
                r"can.*?you.*?add.*?email.*?(\w+(?:\s+\w+)*).*?([^\s]+@[^\s]+\.[^\s]+)"
            ],
            "new_friend": [
                r"met.*?(\w+(?:\s+\w+)*)",
                r"new.*?friend.*?(\w+(?:\s+\w+)*)",
                r"add.*?(\w+(?:\s+\w+)*).*?friend",
                r"introduce.*?(\w+(?:\s+\w+)*)"
            ],
            "update_company": [
                r"(\w+(?:\s+\w+)*).*?works.*?at.*?(\w+(?:\s+\w+)*)",
                r"(\w+(?:\s+\w+)*).*?company.*?(\w+(?:\s+\w+)*)",
                r"update.*?(\w+(?:\s+\w+)*).*?company.*?(\w+(?:\s+\w+)*)"
            ]
        }
        
        message_lower = message.lower().strip()
        
        # Try each pattern type
        for command_type, pattern_list in patterns.items():
            for pattern in pattern_list:
                match = re.search(pattern, message_lower, re.IGNORECASE)
                if match:
                    result = {
                        "command": command_type,
                        "confidence": 0.9
                    }
                    
                    if command_type == "new_friend":
                        result["name"] = match.group(1).strip()
                    elif command_type in ["add_linkedin", "add_email"]:
                        result["name"] = match.group(1).strip()
                        data_value = match.group(2).strip()
                        
                        if command_type == "add_linkedin":
                            result["linkedin"] = data_value
                        elif command_type == "add_email":
                            result["email"] = data_value
                    elif command_type == "update_company":
                        result["name"] = match.group(1).strip()
                        result["company"] = match.group(2).strip()
                    
                    logger.info(f"Returning result: {result}")
                    return result
        
        # If no pattern matches, return a default result
        result = {
            "command": None,
            "name": "unknown",
            "confidence": 0.1
        }
        
        logger.info(f"Returning default result: {result}")
        
        # Return result using the tuple converter to fix Pydantic validation bug
        return create_safe_call_tool_result(json.dumps(result), is_error=False)
    else:
        logger.error(f"Unknown tool: {name}")
        return create_safe_call_tool_result(json.dumps({"error": "Unknown tool"}), is_error=True)

async def main():
    """Run the MCP server"""
    logger.info("Starting final MCP server")
    try:
        async with stdio_server() as (read_stream, write_stream):
            logger.info("stdio_server context entered")
            await server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="final-parser",
                    server_version="1.0.0",
                    capabilities=server.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={}
                    )
                )
            )
    except Exception as e:
        logger.error(f"Error in main: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())

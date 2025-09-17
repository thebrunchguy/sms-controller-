#!/usr/bin/env python3
"""
MCP Server for Complex Admin Command Parsing
Handles natural language admin commands that regex patterns can't parse
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional
from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import (
    CallToolRequest,
    CallToolResult,
    ListToolsRequest,
    ListToolsResult,
    Tool,
    TextContent,
)
from mcp.server import NotificationOptions

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create MCP server
server = Server("admin-command-parser")

# Conversation context storage (in production, use Redis or database)
conversation_contexts: Dict[str, Dict[str, Any]] = {}

@server.list_tools()
async def list_tools() -> ListToolsResult:
    """List available tools for admin command parsing"""
    return ListToolsResult(
        tools=[
            Tool(
                name="parse_admin_command",
                description="Parse complex natural language admin commands and extract structured data",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "message": {
                            "type": "string",
                            "description": "The natural language admin command to parse"
                        },
                        "conversation_id": {
                            "type": "string",
                            "description": "Optional conversation ID for context"
                        }
                    },
                    "required": ["message"]
                }
            ),
            Tool(
                name="get_conversation_context",
                description="Get the current conversation context for a conversation ID",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "conversation_id": {
                            "type": "string",
                            "description": "The conversation ID to get context for"
                        }
                    },
                    "required": ["conversation_id"]
                }
            ),
            Tool(
                name="clear_conversation_context",
                description="Clear conversation context for a conversation ID",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "conversation_id": {
                            "type": "string",
                            "description": "The conversation ID to clear context for"
                        }
                    },
                    "required": ["conversation_id"]
                }
            )
        ]
    )

@server.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> CallToolResult:
    """Handle tool calls"""
    
    try:
        if name == "parse_admin_command":
            return await parse_admin_command(
                arguments.get("message", ""),
                arguments.get("conversation_id")
            )
        elif name == "get_conversation_context":
            return await get_conversation_context(arguments.get("conversation_id", ""))
        elif name == "clear_conversation_context":
            return await clear_conversation_context(arguments.get("conversation_id", ""))
        else:
            raise ValueError(f"Unknown tool: {name}")
    except Exception as e:
        logger.error(f"Error in call_tool for {name}: {e}")
        return CallToolResult(
            content=[
                TextContent(
                    type="text",
                    text=json.dumps({
                        "error": str(e),
                        "command": None,
                        "confidence": 0.0
                    })
                )
            ]
        )

async def parse_admin_command(message: str, conversation_id: Optional[str] = None) -> CallToolResult:
    """Parse complex natural language admin commands"""
    
    try:
        # Get conversation context if provided
        context = {}
        if conversation_id and conversation_id in conversation_contexts:
            context = conversation_contexts[conversation_id]
        
        # Parse the message using LLM-like logic
        parsed_command = await _parse_natural_language_command(message, context)
        
        # Update conversation context if needed
        if conversation_id and parsed_command.get("needs_followup"):
            if conversation_id not in conversation_contexts:
                conversation_contexts[conversation_id] = {}
            conversation_contexts[conversation_id].update(parsed_command.get("context_updates", {}))
        
        return CallToolResult(
            content=[
                TextContent(
                    type="text",
                    text=json.dumps(parsed_command, indent=2)
                )
            ]
        )
        
    except Exception as e:
        logger.error(f"Error parsing admin command: {e}")
        return CallToolResult(
            content=[
                TextContent(
                    type="text",
                    text=json.dumps({
                        "error": str(e),
                        "command": None,
                        "confidence": 0.0
                    })
                )
            ]
        )

async def get_conversation_context(conversation_id: str) -> CallToolResult:
    """Get conversation context"""
    context = conversation_contexts.get(conversation_id, {})
    return CallToolResult(
        content=[
            TextContent(
                type="text",
                text=json.dumps(context, indent=2)
            )
        ]
    )

async def clear_conversation_context(conversation_id: str) -> CallToolResult:
    """Clear conversation context"""
    if conversation_id in conversation_contexts:
        del conversation_contexts[conversation_id]
    
    return CallToolResult(
        content=[
            TextContent(
                type="text",
                text=json.dumps({"status": "cleared", "conversation_id": conversation_id})
            )
        ]
    )

async def _parse_natural_language_command(message: str, context: Dict[str, Any]) -> Dict[str, Any]:
    """Parse natural language command using pattern matching and heuristics"""
    
    try:
        message_lower = message.lower().strip()
        
        # Initialize result
        result = {
            "command": None,
            "name": None,
            "confidence": 0.0,
            "extracted_data": {},
            "needs_followup": False,
            "context_updates": {},
            "response": ""
        }
        
        # Pattern matching for different command types
        patterns = {
            "add_linkedin": [
                r"add.*linkedin.*?(\w+(?:\s+\w+)*).*?(https?://[^\s]+|linkedin\.com/[^\s]+)",
                r"linkedin.*?(\w+(?:\s+\w+)*).*?(https?://[^\s]+|linkedin\.com/[^\s]+)",
                r"(\w+(?:\s+\w+)*).*?linkedin.*?(https?://[^\s]+|linkedin\.com/[^\s]+)"
            ],
            "add_email": [
                r"add.*email.*?(\w+(?:\s+\w+)*).*?([^\s]+@[^\s]+\.[^\s]+)",
                r"email.*?(\w+(?:\s+\w+)*).*?([^\s]+@[^\s]+\.[^\s]+)",
                r"(\w+(?:\s+\w+)*).*?email.*?([^\s]+@[^\s]+\.[^\s]+)"
            ],
            "add_phone": [
                r"add.*phone.*?(\w+(?:\s+\w+)*).*?(\+?[0-9\s\-\(\)]{10,15})",
                r"phone.*?(\w+(?:\s+\w+)*).*?(\+?[0-9\s\-\(\)]{10,15})",
                r"(\w+(?:\s+\w+)*).*?phone.*?(\+?[0-9\s\-\(\)]{10,15})"
            ],
            "add_birthday": [
                r"add.*birthday.*?(\w+(?:\s+\w+)*).*?(\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4}|\d{4}-\d{2}-\d{2})",
                r"birthday.*?(\w+(?:\s+\w+)*).*?(\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4}|\d{4}-\d{2}-\d{2})",
                r"(\w+(?:\s+\w+)*).*?birthday.*?(\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4}|\d{4}-\d{2}-\d{2})"
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
        
        import re
        
        # Try each pattern type
        for command_type, pattern_list in patterns.items():
            for pattern in pattern_list:
                match = re.search(pattern, message_lower, re.IGNORECASE)
                if match:
                    result["command"] = command_type
                    result["confidence"] = 0.8
                    
                    if command_type == "new_friend":
                        result["name"] = match.group(1).strip()
                        result["response"] = f"Adding new friend: {result['name']}"
                    elif command_type in ["add_linkedin", "add_email", "add_phone", "add_birthday"]:
                        result["name"] = match.group(1).strip()
                        data_value = match.group(2).strip()
                        
                        if command_type == "add_linkedin":
                            result["extracted_data"]["linkedin"] = data_value
                            result["response"] = f"Adding LinkedIn {data_value} for {result['name']}"
                        elif command_type == "add_email":
                            result["extracted_data"]["email"] = data_value
                            result["response"] = f"Adding email {data_value} for {result['name']}"
                        elif command_type == "add_phone":
                            result["extracted_data"]["phone"] = data_value
                            result["response"] = f"Adding phone {data_value} for {result['name']}"
                        elif command_type == "add_birthday":
                            result["extracted_data"]["birthday"] = data_value
                            result["response"] = f"Adding birthday {data_value} for {result['name']}"
                    elif command_type == "update_company":
                        result["name"] = match.group(1).strip()
                        result["extracted_data"]["company"] = match.group(2).strip()
                        result["response"] = f"Updating {result['name']}'s company to {result['extracted_data']['company']}"
                    
                    return result
    
        # If no pattern matches, check for follow-up context
        if context.get("waiting_for") and context.get("target_person"):
            result["command"] = context["waiting_for"]
            result["name"] = context["target_person"]
            result["confidence"] = 0.7
            result["needs_followup"] = False
            
            # Extract data based on what we're waiting for
            if context["waiting_for"] == "add_linkedin":
                # Look for URL in message
                url_match = re.search(r'(https?://[^\s]+|linkedin\.com/[^\s]+)', message)
                if url_match:
                    result["extracted_data"]["linkedin"] = url_match.group(1)
                    result["response"] = f"Adding LinkedIn {url_match.group(1)} for {result['name']}"
                else:
                    result["needs_followup"] = True
                    result["response"] = f"What's {result['name']}'s LinkedIn URL?"
            elif context["waiting_for"] == "add_email":
                email_match = re.search(r'([^\s]+@[^\s]+\.[^\s]+)', message)
                if email_match:
                    result["extracted_data"]["email"] = email_match.group(1)
                    result["response"] = f"Adding email {email_match.group(1)} for {result['name']}"
                else:
                    result["needs_followup"] = True
                    result["response"] = f"What's {result['name']}'s email address?"
            
            return result
    
        # If still no match, try to extract a name and ask for clarification
        name_match = re.search(r'(\w+(?:\s+\w+)*)', message_lower)
        if name_match and len(name_match.group(1).split()) >= 2:  # At least first and last name
            result["name"] = name_match.group(1).strip()
            result["needs_followup"] = True
            result["context_updates"] = {
                "target_person": result["name"],
                "waiting_for": "clarification"
            }
            result["response"] = f"I found the name '{result['name']}'. What would you like to do? (add linkedin, email, phone, birthday, etc.)"
            result["confidence"] = 0.5
    
        return result
    except Exception as e:
        logger.error(f"Error in _parse_natural_language_command: {e}")
        return {
            "command": None,
            "name": None,
            "confidence": 0.0,
            "extracted_data": {},
            "needs_followup": False,
            "context_updates": {},
            "response": f"Error parsing: {str(e)}"
        }

async def main():
    """Run the MCP server"""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="admin-command-parser",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={}
                )
            )
        )

if __name__ == "__main__":
    asyncio.run(main())

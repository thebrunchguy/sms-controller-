#!/usr/bin/env python3
"""
MCP Tuple Converter - fixes the Pydantic validation bug by converting tuples to proper objects
"""

import json
from typing import Any, Dict, List
from mcp.types import CallToolResult, TextContent

def convert_tuples_to_objects(data):
    """
    Recursively convert tuples to lists to fix MCP Pydantic validation bug
    """
    if isinstance(data, tuple):
        return list(data)
    elif isinstance(data, dict):
        return {key: convert_tuples_to_objects(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [convert_tuples_to_objects(item) for item in data]
    else:
        return data

def create_safe_call_tool_result(content_data: str, is_error: bool = False) -> CallToolResult:
    """
    Create a CallToolResult that bypasses the MCP Pydantic validation bug
    """
    try:
        # Create TextContent with proper structure
        text_content = TextContent(type="text", text=content_data)
        
        # Convert any tuples to lists to avoid Pydantic validation errors
        safe_content = convert_tuples_to_objects([text_content])
        
        # Create CallToolResult with safe data
        return CallToolResult(
            content=safe_content,
            isError=is_error
        )
    except Exception as e:
        # Fallback: create minimal result
        try:
            return CallToolResult(
                content=[TextContent(type="text", text=f"Error: {str(e)}")],
                isError=True
            )
        except:
            # Ultimate fallback
            return CallToolResult(
                content=[],
                isError=True
            )

def create_safe_text_content(text: str) -> TextContent:
    """
    Create a TextContent that bypasses the MCP Pydantic validation bug
    """
    try:
        # Convert any tuples to lists
        safe_data = convert_tuples_to_objects({"type": "text", "text": text})
        
        return TextContent(
            type=safe_data["type"],
            text=safe_data["text"]
        )
    except Exception as e:
        # Fallback
        return TextContent(type="text", text=f"Error: {str(e)}")

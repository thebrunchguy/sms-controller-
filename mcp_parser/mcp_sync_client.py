#!/usr/bin/env python3
"""
Synchronous MCP client that works within async contexts
"""

import asyncio
import json
import logging
import subprocess
import threading
from typing import Any, Dict
from concurrent.futures import ThreadPoolExecutor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_mcp_in_thread(message: str) -> Dict[str, Any]:
    """
    Run MCP client in a separate thread to avoid async context conflicts
    """
    def _run_mcp():
        try:
            # Import here to avoid circular imports
            from .final_mcp_client import test_final_mcp
            
            # Create new event loop in the thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                result = loop.run_until_complete(test_final_mcp(message))
                return result
            finally:
                loop.close()
                
        except Exception as e:
            logger.error(f"Error in MCP thread: {e}")
            return {
                "error": str(e),
                "command": None,
                "confidence": 0.0
            }
    
    # Run in thread pool to avoid blocking
    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(_run_mcp)
        return future.result(timeout=10)  # 10 second timeout

def test_mcp_sync(message: str) -> Dict[str, Any]:
    """
    Synchronous MCP client that works within async contexts
    """
    try:
        return run_mcp_in_thread(message)
    except Exception as e:
        logger.error(f"Error with sync MCP: {e}")
        return {
            "error": str(e),
            "command": None,
            "confidence": 0.0
        }

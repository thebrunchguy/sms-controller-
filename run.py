#!/usr/bin/env python3
"""
Startup script for the Monthly SMS Check-in Application
"""

import os
import uvicorn
from dotenv import load_dotenv

def main():
    # Load environment variables from config/config.env if it exists
    # On production (Render), environment variables are set directly
    if os.path.exists("config/config.env"):
        load_dotenv("config/config.env")
    else:
        print("No config/config.env file found, using environment variables")
    
    # Configuration
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    reload = os.getenv("APP_ENV", "development") == "development"
    
    print(f"Starting Monthly SMS Check-in Application...")
    print(f"Environment: {os.getenv('APP_ENV', 'development')}")
    print(f"Host: {host}:{port}")
    print(f"Reload: {reload}")
    print(f"API Documentation: http://{host}:{port}/docs")
    
    # Start the server
    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )

if __name__ == "__main__":
    main()

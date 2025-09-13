#!/usr/bin/env python3
"""
Simple keep-alive script for Render service
Run this in the background to keep your service awake
"""

import requests
import time
import os
from datetime import datetime

# Load environment variables
from dotenv import load_dotenv
load_dotenv("config/config.env")

RENDER_APP_URL = os.getenv("APP_BASE_URL", "https://kobro-admin.onrender.com")
HEALTH_CHECK_ENDPOINT = f"{RENDER_APP_URL}/health"
PING_INTERVAL_MINUTES = 5

def ping_service():
    try:
        response = requests.get(HEALTH_CHECK_ENDPOINT, timeout=30)
        if response.status_code == 200:
            data = response.json()
            if data.get("ok") == True:
                print(f"✅ {datetime.now().strftime('%H:%M:%S')} - Service is healthy")
                return True
            else:
                print(f"⚠️  {datetime.now().strftime('%H:%M:%S')} - Service responded but not healthy")
                return False
        else:
            print(f"❌ {datetime.now().strftime('%H:%M:%S')} - HTTP {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"🚨 {datetime.now().strftime('%H:%M:%S')} - Error: {e}")
        return False

def main():
    print("🔄 Starting simple keep-alive service...")
    print(f"📍 Pinging: {HEALTH_CHECK_ENDPOINT}")
    print(f"⏰ Interval: Every {PING_INTERVAL_MINUTES} minutes")
    print("🛑 Press Ctrl+C to stop")
    print("-" * 50)
    
    # Run immediately on startup
    ping_service()
    
    while True:
        time.sleep(PING_INTERVAL_MINUTES * 60)  # Convert minutes to seconds
        ping_service()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n🛑 Keep-alive service stopped at {datetime.now().strftime('%H:%M:%S')}")

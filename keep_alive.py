#!/usr/bin/env python3
"""
Keep-alive script for Render free tier
Pings the health endpoint every 10 minutes to prevent sleep
"""

import requests
import time
import schedule
import threading
from datetime import datetime

def ping_health():
    """Ping the health endpoint to keep service awake"""
    try:
        response = requests.get("https://kobro-admin.onrender.com/health", timeout=30)
        if response.status_code == 200:
            print(f"✅ {datetime.now().strftime('%H:%M:%S')} - Health check successful")
        else:
            print(f"⚠️  {datetime.now().strftime('%H:%M:%S')} - Health check failed: {response.status_code}")
    except Exception as e:
        print(f"❌ {datetime.now().strftime('%H:%M:%S')} - Health check error: {e}")

def run_scheduler():
    """Run the scheduler in a separate thread"""
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    print("🔄 Starting keep-alive service for Render...")
    print("📍 Pinging: https://kobro-admin.onrender.com/health")
    print("⏰ Interval: Every 10 minutes")
    print("🛑 Press Ctrl+C to stop")
    
    # Schedule health checks every 10 minutes
    schedule.every(10).minutes.do(ping_health)
    
    # Run first ping immediately
    ping_health()
    
    # Start scheduler in background thread
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()
    
    try:
        # Keep main thread alive
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        print("\n🛑 Keep-alive service stopped")

#!/usr/bin/env python3
"""
Robust keep-alive script for Render free tier
Auto-restarts on errors and handles network issues
"""

import requests
import time
import schedule
import threading
import signal
import sys
from datetime import datetime

class KeepAliveService:
    def __init__(self):
        self.running = True
        self.url = "https://kobro-admin.onrender.com/health"
        self.ping_count = 0
        self.error_count = 0
        self.max_errors = 5
        
    def ping_health(self):
        """Ping the health endpoint to keep service awake"""
        try:
            self.ping_count += 1
            response = requests.get(self.url, timeout=30)
            
            if response.status_code == 200:
                print(f"✅ {datetime.now().strftime('%H:%M:%S')} - Ping #{self.ping_count} successful")
                self.error_count = 0  # Reset error count on success
            else:
                self.error_count += 1
                print(f"⚠️  {datetime.now().strftime('%H:%M:%S')} - Ping #{self.ping_count} failed: {response.status_code}")
                
        except Exception as e:
            self.error_count += 1
            print(f"❌ {datetime.now().strftime('%H:%M:%S')} - Ping #{self.ping_count} error: {e}")
            
        # Check if we've hit max errors
        if self.error_count >= self.max_errors:
            print(f"🚨 Too many errors ({self.error_count}), restarting in 60 seconds...")
            time.sleep(60)
            self.error_count = 0
            self.ping_count = 0
    
    def run_scheduler(self):
        """Run the scheduler in a separate thread"""
        while self.running:
            try:
                schedule.run_pending()
                time.sleep(1)
            except Exception as e:
                print(f"❌ Scheduler error: {e}")
                time.sleep(5)  # Wait before retrying
    
    def signal_handler(self, signum, frame):
        """Handle Ctrl+C gracefully"""
        print(f"\n🛑 Received signal {signum}, stopping keep-alive service...")
        self.running = False
        sys.exit(0)
    
    def start(self):
        """Start the keep-alive service"""
        print("🔄 Starting robust keep-alive service for Render...")
        print(f"📍 Pinging: {self.url}")
        print("⏰ Interval: Every 10 minutes")
        print("🔄 Auto-restart: On errors")
        print("🛑 Press Ctrl+C to stop")
        
        # Set up signal handler for graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        # Schedule health checks every 10 minutes
        schedule.every(10).minutes.do(self.ping_health)
        
        # Run first ping immediately
        self.ping_health()
        
        # Start scheduler in background thread
        scheduler_thread = threading.Thread(target=self.run_scheduler, daemon=True)
        scheduler_thread.start()
        
        try:
            # Keep main thread alive
            while self.running:
                time.sleep(60)
        except KeyboardInterrupt:
            self.signal_handler(signal.SIGINT, None)

if __name__ == "__main__":
    service = KeepAliveService()
    service.start()

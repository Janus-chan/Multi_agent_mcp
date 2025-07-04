#!/usr/bin/env python3
"""
Complete system startup script for OCR Agent with File Upload Client.
Starts both the OCR agent server and the file upload client.
"""

import asyncio
import subprocess
import sys
import time
import requests
import logging
import signal
import os
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SystemManager:
    """Manages the complete OCR system with both servers."""
    
    def __init__(self):
        self.ocr_process = None
        self.upload_process = None
        self.running = True
        
    def check_server_health(self, url: str, max_retries: int = 15, delay: int = 2) -> bool:
        """Check if a server is running and healthy."""
        for attempt in range(max_retries):
            try:
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    return True
            except requests.exceptions.RequestException:
                pass
            
            if attempt < max_retries - 1:
                logger.info(f"⏳ Waiting for server at {url}... (attempt {attempt + 1}/{max_retries})")
                time.sleep(delay)
        
        return False
    
    def start_ocr_agent(self):
        """Start the OCR agent server."""
        logger.info("🚀 Starting OCR Agent server...")
        
        ocr_agent_dir = Path(__file__).parent / "ocr_agent"
        if not ocr_agent_dir.exists():
            logger.error(f"❌ OCR agent directory not found: {ocr_agent_dir}")
            return False
        
        try:
            cmd = [sys.executable, "_main_.py", "--host", "localhost", "--port", "8003"]
            self.ocr_process = subprocess.Popen(
                cmd,
                cwd=ocr_agent_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Check if process started successfully
            time.sleep(3)
            if self.ocr_process.poll() is not None:
                stdout, stderr = self.ocr_process.communicate()
                logger.error(f"❌ OCR agent failed to start")
                logger.error(f"STDOUT: {stdout}")
                logger.error(f"STDERR: {stderr}")
                return False
            
            # Wait for server to be healthy
            if self.check_server_health("http://localhost:8003/.well-known/agent.json"):
                logger.info("✅ OCR Agent server is running on http://localhost:8003")
                return True
            else:
                logger.error("❌ OCR Agent server failed to become healthy")
                self.stop_ocr_agent()
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to start OCR agent: {e}")
            return False
    
    def start_file_upload_client(self):
        """Start the file upload client."""
        logger.info("🚀 Starting File Upload Client...")
        
        try:
            cmd = [sys.executable, "file_upload_client.py", "--port", "8004", 
                   "--ocr-agent-url", "http://localhost:8003"]
            self.upload_process = subprocess.Popen(
                cmd,
                cwd=Path(__file__).parent,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Check if process started successfully
            time.sleep(3)
            if self.upload_process.poll() is not None:
                stdout, stderr = self.upload_process.communicate()
                logger.error(f"❌ File upload client failed to start")
                logger.error(f"STDOUT: {stdout}")
                logger.error(f"STDERR: {stderr}")
                return False
            
            # Wait for server to be healthy
            if self.check_server_health("http://localhost:8004/health"):
                logger.info("✅ File Upload Client is running on http://localhost:8004")
                return True
            else:
                logger.error("❌ File Upload Client failed to become healthy")
                self.stop_upload_client()
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to start file upload client: {e}")
            return False
    
    def stop_ocr_agent(self):
        """Stop the OCR agent server."""
        if self.ocr_process:
            logger.info("🛑 Stopping OCR Agent server...")
            self.ocr_process.terminate()
            try:
                self.ocr_process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                logger.warning("⚠️  Force killing OCR agent process")
                self.ocr_process.kill()
            self.ocr_process = None
    
    def stop_upload_client(self):
        """Stop the file upload client."""
        if self.upload_process:
            logger.info("🛑 Stopping File Upload Client...")
            self.upload_process.terminate()
            try:
                self.upload_process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                logger.warning("⚠️  Force killing upload client process")
                self.upload_process.kill()
            self.upload_process = None
    
    def stop_all(self):
        """Stop all services."""
        self.running = False
        self.stop_upload_client()
        self.stop_ocr_agent()
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        logger.info(f"\n🛑 Received signal {signum}, shutting down...")
        self.stop_all()
    
    def monitor_processes(self):
        """Monitor running processes and restart if needed."""
        while self.running:
            try:
                # Check OCR agent
                if self.ocr_process and self.ocr_process.poll() is not None:
                    logger.warning("⚠️  OCR agent process has stopped unexpectedly")
                    self.running = False
                    break
                
                # Check upload client
                if self.upload_process and self.upload_process.poll() is not None:
                    logger.warning("⚠️  File upload client process has stopped unexpectedly")
                    self.running = False
                    break
                
                time.sleep(2)
                
            except KeyboardInterrupt:
                logger.info("\n🛑 Keyboard interrupt received")
                self.stop_all()
                break
    
    def start_system(self):
        """Start the complete system."""
        # Set up signal handlers
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        logger.info("🎯 Starting Complete OCR System...")
        logger.info("=" * 50)
        
        # Start OCR agent first
        if not self.start_ocr_agent():
            logger.error("❌ Failed to start OCR agent. Aborting.")
            return False
        
        # Start file upload client
        if not self.start_file_upload_client():
            logger.error("❌ Failed to start file upload client. Stopping OCR agent.")
            self.stop_ocr_agent()
            return False
        
        # System is ready
        logger.info("🎉 Complete OCR System is running!")
        logger.info("=" * 50)
        logger.info("📋 System Status:")
        logger.info("  ✅ OCR Agent Server: http://localhost:8003")
        logger.info("  ✅ File Upload Client: http://localhost:8004")
        logger.info("")
        logger.info("🔗 Available Endpoints:")
        logger.info("  📤 File Upload: http://localhost:8004/upload")
        logger.info("  ℹ️  Upload Info: http://localhost:8004/")
        logger.info("  🔍 OCR Agent Card: http://localhost:8003/.well-known/agent.json")
        logger.info("  ❤️  Health Checks: http://localhost:8004/health")
        logger.info("")
        logger.info("📋 Testing Options:")
        logger.info("  1. Use Postman with file uploads (see FILE_UPLOAD_TESTING_GUIDE.md)")
        logger.info("  2. Import OCR_File_Upload_Tests.postman_collection.json")
        logger.info("  3. Visit http://localhost:8004/ for usage instructions")
        logger.info("")
        logger.info("🛑 Press Ctrl+C to stop all services")
        logger.info("=" * 50)
        
        # Monitor processes
        try:
            self.monitor_processes()
        except Exception as e:
            logger.error(f"❌ System monitoring error: {e}")
        finally:
            self.stop_all()
        
        logger.info("✅ System shutdown complete")
        return True

def main():
    """Main function."""
    print("Complete OCR System Startup")
    print("=" * 30)
    print("This script starts both:")
    print("  1. OCR Agent Server (port 8003)")
    print("  2. File Upload Client (port 8004)")
    print()
    
    # Check prerequisites
    if not Path("ocr_agent").exists():
        print("❌ Error: ocr_agent directory not found!")
        print("Please run this script from the Multi_agent_mcp directory.")
        sys.exit(1)
    
    if not Path("file_upload_client.py").exists():
        print("❌ Error: file_upload_client.py not found!")
        print("Please ensure all files are in the Multi_agent_mcp directory.")
        sys.exit(1)
    
    print("✅ Prerequisites check passed")
    print("🚀 Starting system...")
    print()
    
    manager = SystemManager()
    success = manager.start_system()
    
    if not success:
        print("\n❌ System startup failed")
        sys.exit(1)

if __name__ == "__main__":
    main()

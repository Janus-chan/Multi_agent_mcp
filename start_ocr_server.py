#!/usr/bin/env python3
"""
Simple script to start the OCR agent server for testing.
"""

import sys
import os
import subprocess
import time
import requests
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_server_health(url: str, max_retries: int = 10, delay: int = 2) -> bool:
    """Check if the server is running and healthy."""
    for attempt in range(max_retries):
        try:
            response = requests.get(f"{url}/.well-known/agent.json", timeout=5)
            if response.status_code == 200:
                logger.info(f"✅ Server is healthy and responding at {url}")
                return True
        except requests.exceptions.RequestException:
            pass
        
        if attempt < max_retries - 1:
            logger.info(f"⏳ Waiting for server to start... (attempt {attempt + 1}/{max_retries})")
            time.sleep(delay)
    
    return False

def start_ocr_server(host: str = "localhost", port: int = 8003):
    """Start the OCR agent server."""
    
    # Change to the ocr_agent directory
    ocr_agent_dir = os.path.join(os.path.dirname(__file__), "ocr_agent")
    
    if not os.path.exists(ocr_agent_dir):
        logger.error(f"❌ OCR agent directory not found: {ocr_agent_dir}")
        return False
    
    logger.info(f"🚀 Starting OCR agent server on {host}:{port}")
    logger.info(f"📁 Working directory: {ocr_agent_dir}")
    
    try:
        # Start the server process
        cmd = [sys.executable, "_main_.py", "--host", host, "--port", str(port)]
        logger.info(f"🔧 Running command: {' '.join(cmd)}")
        
        process = subprocess.Popen(
            cmd,
            cwd=ocr_agent_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        # Give the server a moment to start
        time.sleep(3)
        
        # Check if process is still running
        if process.poll() is not None:
            stdout, stderr = process.communicate()
            logger.error(f"❌ Server process exited early")
            logger.error(f"STDOUT: {stdout}")
            logger.error(f"STDERR: {stderr}")
            return False
        
        # Check server health
        server_url = f"http://{host}:{port}"
        if check_server_health(server_url):
            logger.info(f"🎉 OCR agent server is running successfully!")
            logger.info(f"🌐 Agent card: {server_url}/.well-known/agent.json")
            logger.info(f"🔗 A2A endpoint: {server_url}/a2a/ocr_agent")
            logger.info(f"📋 Use Ctrl+C to stop the server")
            
            try:
                # Keep the server running and show logs
                while True:
                    # Read and display server output
                    output = process.stdout.readline()
                    if output:
                        print(f"[SERVER] {output.strip()}")
                    
                    # Check if process is still alive
                    if process.poll() is not None:
                        logger.warning("⚠️  Server process has stopped")
                        break
                        
                    time.sleep(0.1)
                    
            except KeyboardInterrupt:
                logger.info("🛑 Stopping server...")
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    logger.warning("⚠️  Force killing server process")
                    process.kill()
                logger.info("✅ Server stopped")
                return True
        else:
            logger.error(f"❌ Server failed to start or is not responding")
            process.terminate()
            return False
            
    except Exception as e:
        logger.error(f"❌ Failed to start server: {e}")
        return False

def main():
    """Main function."""
    print("OCR Agent Server Starter")
    print("=" * 30)
    print("This script starts the OCR agent server for testing.")
    print("The server will run on http://localhost:8003")
    print()
    
    # Check if we're in the right directory
    if not os.path.exists("ocr_agent"):
        print("❌ Error: ocr_agent directory not found!")
        print("Please run this script from the Multi_agent_mcp directory.")
        sys.exit(1)
    
    # Check if required files exist
    main_file = os.path.join("ocr_agent", "_main_.py")
    if not os.path.exists(main_file):
        print(f"❌ Error: {main_file} not found!")
        print("Please ensure the OCR agent files are properly set up.")
        sys.exit(1)
    
    print("✅ Prerequisites check passed")
    print("🚀 Starting OCR agent server...")
    print()
    
    success = start_ocr_server()
    
    if success:
        print("\n🎉 Server session completed successfully")
    else:
        print("\n❌ Server failed to start or encountered an error")
        sys.exit(1)

if __name__ == "__main__":
    main()

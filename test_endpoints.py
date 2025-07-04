#!/usr/bin/env python3
"""
Test script to verify OCR agent and file upload client endpoints are working.
"""

import requests
import json
import time

def test_ocr_agent_endpoints():
    """Test OCR agent endpoints."""
    print("🔍 Testing OCR Agent Endpoints...")
    
    base_url = "http://localhost:8003"
    
    # Test agent card
    try:
        response = requests.get(f"{base_url}/.well-known/agent.json", timeout=5)
        if response.status_code == 200:
            print("✅ Agent card endpoint working")
            agent_card = response.json()
            print(f"   Agent: {agent_card.get('name', 'Unknown')}")
        else:
            print(f"❌ Agent card failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Agent card error: {e}")
    
    # Test A2A endpoint with simple request
    try:
        test_payload = {
            "task_id": "test-123",
            "context_id": "test-context-123", 
            "user_input": "Test OCR processing",
            "timestamp": int(time.time() * 1000)
        }
        
        response = requests.post(
            f"{base_url}/a2a/ocr_agent",
            json=test_payload,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 200:
            print("✅ A2A endpoint working")
            result = response.json()
            print(f"   Response task_id: {result.get('task_id', 'None')}")
        else:
            print(f"❌ A2A endpoint failed: {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"❌ A2A endpoint error: {e}")

def test_file_upload_client():
    """Test file upload client endpoints."""
    print("\n📤 Testing File Upload Client Endpoints...")
    
    base_url = "http://localhost:8004"
    
    # Test health endpoint
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Health endpoint working")
            health = response.json()
            print(f"   Status: {health.get('status', 'Unknown')}")
        else:
            print(f"❌ Health endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Health endpoint error: {e}")
    
    # Test info page
    try:
        response = requests.get(f"{base_url}/", timeout=5)
        if response.status_code == 200:
            print("✅ Info page working")
        else:
            print(f"❌ Info page failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Info page error: {e}")

def test_integration():
    """Test integration between services."""
    print("\n🔗 Testing Service Integration...")
    
    # Create a simple test file
    test_content = b"This is a test file for OCR processing"
    
    try:
        # Test file upload without actual file (should fail gracefully)
        response = requests.post(
            "http://localhost:8004/upload",
            data={"user_id": "test_user", "description": "Integration test"},
            timeout=10
        )
        
        if response.status_code == 400:
            print("✅ File upload validation working (correctly rejected empty upload)")
            error_response = response.json()
            print(f"   Error: {error_response.get('error', 'Unknown')}")
        else:
            print(f"⚠️  Unexpected response: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Integration test error: {e}")

def main():
    """Main test function."""
    print("🧪 OCR System Endpoint Testing")
    print("=" * 40)
    print("This script tests if both services are running and accessible.")
    print()
    
    # Test OCR agent
    test_ocr_agent_endpoints()
    
    # Test file upload client
    test_file_upload_client()
    
    # Test integration
    test_integration()
    
    print("\n" + "=" * 40)
    print("📋 Test Summary:")
    print("If you see ✅ for most tests, your services are working correctly!")
    print("If you see ❌ errors:")
    print("  1. Make sure both services are running")
    print("  2. Check the service logs for detailed error messages")
    print("  3. Verify ports 8003 and 8004 are not blocked")
    print()
    print("🚀 Next steps:")
    print("  1. Use Postman to upload actual image files")
    print("  2. Import OCR_File_Upload_Tests.postman_collection.json")
    print("  3. Test with real images for OCR processing")

if __name__ == "__main__":
    main()

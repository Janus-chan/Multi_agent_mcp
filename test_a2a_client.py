#!/usr/bin/env python3
"""
A2A Client for testing the OCR Agent with image array processing.
This script connects to the OCR agent server and tests various scenarios.
"""

import asyncio
import json
import logging
import time
from typing import Dict, List, Any
import aiohttp
import uuid

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class A2AOCRClient:
    """A2A client for testing OCR agent functionality."""
    
    def __init__(self, base_url: str = "http://localhost:8003"):
        self.base_url = base_url
        self.session = None
        
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    async def get_agent_card(self) -> Dict[str, Any]:
        """Get the agent card information."""
        try:
            async with self.session.get(f"{self.base_url}/.well-known/agent.json") as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.error(f"Failed to get agent card: {response.status}")
                    return {}
        except Exception as e:
            logger.error(f"Error getting agent card: {e}")
            return {}
    
    async def send_ocr_request(self, input_data: Any, task_id: str = None) -> Dict[str, Any]:
        """Send OCR processing request to the agent."""
        if task_id is None:
            task_id = str(uuid.uuid4())
        
        # Prepare the A2A request payload
        payload = {
            "task_id": task_id,
            "context_id": str(uuid.uuid4()),
            "user_input": json.dumps(input_data) if isinstance(input_data, (list, dict)) else str(input_data),
            "timestamp": int(time.time() * 1000)
        }
        
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        try:
            # Send request to the A2A endpoint
            async with self.session.post(
                f"{self.base_url}/a2a/ocr_agent",
                json=payload,
                headers=headers
            ) as response:
                
                logger.info(f"Request sent - Status: {response.status}")
                
                if response.status == 200:
                    result = await response.json()
                    return result
                else:
                    error_text = await response.text()
                    logger.error(f"Request failed: {response.status} - {error_text}")
                    return {"error": f"HTTP {response.status}", "details": error_text}
                    
        except Exception as e:
            logger.error(f"Error sending request: {e}")
            return {"error": "Request failed", "details": str(e)}

async def test_image_array_processing():
    """Test image array processing functionality."""
    print("\n" + "="*60)
    print("TESTING IMAGE ARRAY PROCESSING")
    print("="*60)
    
    async with A2AOCRClient() as client:
        # Test 1: Image array with mixed formats
        test_images = [
            {
                "path": "/path/to/invoice.jpg",
                "name": "Invoice Document",
                "description": "Company invoice for processing"
            },
            {
                "path": "/path/to/screenshot.png", 
                "name": "App Screenshot",
                "description": "Application interface screenshot"
            },
            "/path/to/document.pdf",  # Simple string format
            {
                "file": "/path/to/receipt.jpg",  # Alternative 'file' key
                "name": "Receipt",
                "description": "Purchase receipt"
            }
        ]
        
        print(f"Sending image array with {len(test_images)} images:")
        print(json.dumps(test_images, indent=2))
        
        result = await client.send_ocr_request(test_images)
        
        print("\nResponse received:")
        print(json.dumps(result, indent=2))
        
        return result

async def test_single_text_input():
    """Test single text input processing."""
    print("\n" + "="*60)
    print("TESTING SINGLE TEXT INPUT")
    print("="*60)
    
    async with A2AOCRClient() as client:
        test_text = "Please process this image for OCR analysis"
        
        print(f"Sending text input: '{test_text}'")
        
        result = await client.send_ocr_request(test_text)
        
        print("\nResponse received:")
        print(json.dumps(result, indent=2))
        
        return result

async def test_single_image_object():
    """Test single image object processing."""
    print("\n" + "="*60)
    print("TESTING SINGLE IMAGE OBJECT")
    print("="*60)
    
    async with A2AOCRClient() as client:
        test_image = {
            "path": "/path/to/single_document.jpg",
            "name": "Single Document",
            "description": "A single document for OCR processing"
        }
        
        print(f"Sending single image object:")
        print(json.dumps(test_image, indent=2))
        
        result = await client.send_ocr_request(test_image)
        
        print("\nResponse received:")
        print(json.dumps(result, indent=2))
        
        return result

async def test_agent_connectivity():
    """Test basic connectivity to the agent."""
    print("\n" + "="*60)
    print("TESTING AGENT CONNECTIVITY")
    print("="*60)
    
    async with A2AOCRClient() as client:
        # Test agent card endpoint
        agent_card = await client.get_agent_card()
        
        if agent_card:
            print("✅ Agent card retrieved successfully:")
            print(json.dumps(agent_card, indent=2))
            return True
        else:
            print("❌ Failed to retrieve agent card")
            return False

async def run_comprehensive_tests():
    """Run all tests in sequence."""
    print("🚀 Starting comprehensive OCR Agent tests...")
    
    # Test 1: Basic connectivity
    connectivity_ok = await test_agent_connectivity()
    
    if not connectivity_ok:
        print("\n❌ Connectivity test failed. Make sure the OCR agent server is running on http://localhost:8003")
        return
    
    # Test 2: Image array processing
    await test_image_array_processing()
    
    # Test 3: Single text input
    await test_single_text_input()
    
    # Test 4: Single image object
    await test_single_image_object()
    
    print("\n" + "="*60)
    print("🎉 ALL TESTS COMPLETED")
    print("="*60)
    print("\nTest Summary:")
    print("✅ Agent connectivity test")
    print("✅ Image array processing test")
    print("✅ Single text input test")
    print("✅ Single image object test")
    print("\nIf all tests show proper JSON responses with 'status': 'success',")
    print("your OCR agent modifications are working correctly!")

if __name__ == "__main__":
    print("OCR Agent A2A Client Test Suite")
    print("=" * 40)
    print("This script tests the modified OCR agent with various input types.")
    print("Make sure the OCR agent server is running before starting tests.")
    print("\nStarting tests in 3 seconds...")
    
    try:
        asyncio.run(run_comprehensive_tests())
    except KeyboardInterrupt:
        print("\n\n⏹️  Tests interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Test suite failed with error: {e}")
        logger.error("Test suite error", exc_info=True)

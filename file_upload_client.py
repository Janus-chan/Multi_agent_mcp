#!/usr/bin/env python3
"""
A2A File Upload Client for OCR Agent
Handles multipart/form-data file uploads and forwards to OCR agent with proper A2A protocol.
"""

import asyncio
import json
import logging
import time
import uuid
from typing import List, Dict, Any, Optional
from pathlib import Path
import tempfile
import os

import aiohttp
from aiohttp import web, FormData
from aiohttp.web_request import Request
from aiohttp.web_response import Response
import aiofiles
from aiohttp.multipart import MultipartReader, BodyPartReader

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class A2AFileUploadClient:
    """A2A client that handles file uploads and forwards to OCR agent."""
    
    def __init__(self, ocr_agent_url: str = "http://localhost:8003", client_port: int = 8004):
        self.ocr_agent_url = ocr_agent_url
        self.client_port = client_port
        self.app = web.Application()
        self.setup_routes()
        
    def setup_routes(self):
        """Setup HTTP routes for the file upload client."""
        self.app.router.add_post('/upload', self.handle_file_upload)
        self.app.router.add_get('/health', self.health_check)
        self.app.router.add_get('/', self.info_page)
        
    async def health_check(self, request: Request) -> Response:
        """Health check endpoint."""
        return web.json_response({
            "status": "healthy",
            "service": "A2A File Upload Client",
            "ocr_agent_url": self.ocr_agent_url,
            "timestamp": int(time.time() * 1000)
        })
    
    async def info_page(self, request: Request) -> Response:
        """Information page with usage instructions."""
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>A2A File Upload Client</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; }
                .container { max-width: 800px; }
                .endpoint { background: #f5f5f5; padding: 10px; border-radius: 5px; margin: 10px 0; }
                .method { color: #007acc; font-weight: bold; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>A2A File Upload Client for OCR Processing</h1>
                <p>This service accepts file uploads and forwards them to the OCR agent with proper A2A protocol.</p>
                
                <h2>Endpoints</h2>
                <div class="endpoint">
                    <span class="method">POST</span> /upload - Upload files for OCR processing
                </div>
                <div class="endpoint">
                    <span class="method">GET</span> /health - Health check
                </div>
                
                <h2>Usage with Postman</h2>
                <ol>
                    <li>Set method to <strong>POST</strong></li>
                    <li>Set URL to <strong>http://localhost:8004/upload</strong></li>
                    <li>Go to <strong>Body</strong> tab</li>
                    <li>Select <strong>form-data</strong></li>
                    <li>Add files with key <strong>"files"</strong></li>
                    <li>Optionally add metadata fields</li>
                    <li>Send request</li>
                </ol>
                
                <h2>Optional Form Fields</h2>
                <ul>
                    <li><strong>user_id</strong> - Custom user ID (auto-generated if not provided)</li>
                    <li><strong>description</strong> - Description for the processing task</li>
                </ul>
                
                <p><strong>OCR Agent URL:</strong> {ocr_agent_url}</p>
            </div>
        </body>
        </html>
        """.format(ocr_agent_url=self.ocr_agent_url)
        
        return web.Response(text=html_content, content_type='text/html')
    
    async def handle_file_upload(self, request: Request) -> Response:
        """Handle multipart file upload and forward to OCR agent."""
        try:
            # Generate A2A protocol fields automatically
            task_id = str(uuid.uuid4())
            context_id = str(uuid.uuid4())
            timestamp = int(time.time() * 1000)
            
            logger.info(f"Processing file upload request - Task ID: {task_id}")
            
            # Parse multipart form data
            reader = await request.multipart()
            files = []
            user_id = f"upload_user_{int(time.time())}"
            description = "File upload OCR processing"
            
            temp_files = []  # Track temporary files for cleanup
            
            async for field in reader:
                # Check if field is None or is not a BodyPartReader
                if field is None or not isinstance(field, BodyPartReader):
                    continue
                    
                field_name = getattr(field, 'name', None)
                if field_name is None:
                    continue
                
                if field_name == 'files':
                    # Handle uploaded file
                    field_filename = getattr(field, 'filename', None)
                    if field_filename:
                        # Save file temporarily
                        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=f"_{field_filename}")
                        temp_files.append(temp_file.name)
                        
                        async with aiofiles.open(temp_file.name, 'wb') as f:
                            async for chunk in field:
                                # Ensure chunk is bytes
                                if isinstance(chunk, bytes):
                                    await f.write(chunk)
                                else:
                                    logger.warning(f"Unexpected chunk type: {type(chunk)}")
                        
                        # Create file metadata
                        file_info = {
                            "path": temp_file.name,
                            "name": field_filename,
                            "description": f"Uploaded file: {field_filename}",
                            "original_filename": field_filename,
                            "upload_timestamp": timestamp
                        }
                        files.append(file_info)
                        
                        logger.info(f"Received file: {field_filename} ({os.path.getsize(temp_file.name)} bytes)")
                
                elif field_name == 'user_id':
                    # Custom user ID
                    try:
                        content = await field.read()
                        if isinstance(content, bytes):
                            user_id = content.decode().strip()
                    except Exception as e:
                        logger.warning(f"Failed to read user_id field: {e}")
                        
                elif field_name == 'description':
                    # Custom description
                    try:
                        content = await field.read()
                        if isinstance(content, bytes):
                            description = content.decode().strip()
                    except Exception as e:
                        logger.warning(f"Failed to read description field: {e}")
            
            if not files:
                return web.json_response({
                    "error": "No files uploaded",
                    "message": "Please upload at least one file using the 'files' field"
                }, status=400)
            
            logger.info(f"Processing {len(files)} uploaded files")
            
            # Forward to OCR agent
            ocr_result = await self.forward_to_ocr_agent(
                files=files,
                task_id=task_id,
                context_id=context_id,
                user_id=user_id,
                timestamp=timestamp,
                description=description
            )
            
            # Cleanup temporary files
            for temp_file in temp_files:
                try:
                    os.unlink(temp_file)
                except OSError:
                    logger.warning(f"Failed to cleanup temp file: {temp_file}")
            
            # Return response with A2A metadata
            response = {
                "task_id": task_id,
                "context_id": context_id,
                "user_id": user_id,
                "timestamp": timestamp,
                "uploaded_files": len(files),
                "files_info": [{"name": f["name"], "original_filename": f["original_filename"]} for f in files],
                "ocr_result": ocr_result,
                "status": "completed"
            }
            
            logger.info(f"File upload processing completed - Task ID: {task_id}")
            return web.json_response(response)
            
        except Exception as e:
            logger.error(f"Error processing file upload: {e}", exc_info=True)
            return web.json_response({
                "error": "File upload processing failed",
                "message": str(e),
                "task_id": task_id if 'task_id' in locals() else None
            }, status=500)
    
    async def forward_to_ocr_agent(self, files: List[Dict], task_id: str, context_id: str, 
                                 user_id: str, timestamp: int, description: str) -> Dict[str, Any]:
        """Forward the processed files to the OCR agent using A2A protocol."""
        try:
            # Prepare A2A request payload
            a2a_payload = {
                "task_id": task_id,
                "context_id": context_id,
                "user_id": user_id,
                "timestamp": timestamp,
                "user_input": json.dumps(files),  # Convert file array to JSON string
                "metadata": {
                    "source": "file_upload_client",
                    "description": description,
                    "file_count": len(files)
                }
            }
            
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json",
                "User-Agent": "A2A-FileUpload-Client/1.0"
            }
            
            logger.info(f"Forwarding to OCR agent: {self.ocr_agent_url}/a2a/ocr_agent")
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.ocr_agent_url}/a2a/ocr_agent",
                    json=a2a_payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=60)  # 60 second timeout
                ) as response:
                    
                    if response.status == 200:
                        result = await response.json()
                        logger.info(f"OCR agent responded successfully")
                        return result
                    else:
                        error_text = await response.text()
                        logger.error(f"OCR agent error: {response.status} - {error_text}")
                        return {
                            "error": f"OCR agent returned status {response.status}",
                            "details": error_text
                        }
                        
        except asyncio.TimeoutError:
            logger.error("Timeout waiting for OCR agent response")
            return {"error": "OCR processing timeout", "details": "The OCR agent took too long to respond"}
            
        except Exception as e:
            logger.error(f"Error forwarding to OCR agent: {e}", exc_info=True)
            return {"error": "Failed to communicate with OCR agent", "details": str(e)}
    
    async def start_server(self):
        """Start the file upload client server."""
        runner = web.AppRunner(self.app)
        await runner.setup()
        
        site = web.TCPSite(runner, 'localhost', self.client_port)
        await site.start()
        
        logger.info(f"🚀 A2A File Upload Client started on http://localhost:{self.client_port}")
        logger.info(f"📁 Upload endpoint: http://localhost:{self.client_port}/upload")
        logger.info(f"🔗 OCR Agent URL: {self.ocr_agent_url}")
        logger.info(f"ℹ️  Info page: http://localhost:{self.client_port}/")
        
        return runner

async def main():
    """Main function to start the file upload client."""
    import argparse
    
    parser = argparse.ArgumentParser(description="A2A File Upload Client for OCR Agent")
    parser.add_argument("--port", type=int, default=8004, help="Port for the file upload client")
    parser.add_argument("--ocr-agent-url", default="http://localhost:8003", 
                       help="URL of the OCR agent server")
    
    args = parser.parse_args()
    
    print("A2A File Upload Client for OCR Processing")
    print("=" * 45)
    print(f"Client Port: {args.port}")
    print(f"OCR Agent URL: {args.ocr_agent_url}")
    print()
    
    client = A2AFileUploadClient(
        ocr_agent_url=args.ocr_agent_url,
        client_port=args.port
    )
    
    try:
        runner = await client.start_server()
        
        print("✅ Server started successfully!")
        print(f"📤 Upload files at: http://localhost:{args.port}/upload")
        print(f"🌐 Info page: http://localhost:{args.port}/")
        print("📋 Use Ctrl+C to stop the server")
        print()
        
        # Keep the server running
        while True:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        print("\n🛑 Stopping server...")
        if 'runner' in locals():
            await runner.cleanup()
        print("✅ Server stopped")

if __name__ == "__main__":
    asyncio.run(main())

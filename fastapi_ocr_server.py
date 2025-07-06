#!/usr/bin/env python3
"""
FastAPI OCR Server

A FastAPI-based HTTP API server that accepts multipart file uploads and forwards them 
to the A2A OCR agent using the enhanced A2A client.

This implements the two-layer architecture:
- Layer 1: HTTP API server (this file) that receives files from Postman/HTTP clients
- Layer 2: A2A client that communicates with the OCR agent server

Features:
- Accept multiple image files via multipart/form-data
- Support various image formats (JPG, PNG, PDF, TIFF, BMP, GIF, WEBP)
- File validation and error handling
- Progress tracking and logging
- Comprehensive API documentation with Swagger UI

Usage:
    python fastapi_ocr_server.py --port 8005 --ocr-server http://localhost:8003
"""

import asyncio
import json
import logging
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from uuid import uuid4

import uvicorn
from fastapi import FastAPI, File, Form, HTTPException, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# Import our enhanced A2A client and file utilities
from a2a_ocr_client import A2AOCRClient
from file_utils import SUPPORTED_IMAGE_FORMATS, MAX_FILE_SIZE

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Pydantic models for API documentation
class OCRRequest(BaseModel):
    """OCR processing request model."""
    user_id: Optional[str] = None
    context_id: Optional[str] = None
    description: Optional[str] = None
    include_file_data: bool = False

class OCRResponse(BaseModel):
    """OCR processing response model."""
    status: str
    task_id: str
    user_id: str
    context_id: Optional[str]
    processing_time: float
    file_count: int
    results: Union[Dict[str, Any], List[Dict[str, Any]], str]
    error: Optional[str] = None

class HealthResponse(BaseModel):
    """Health check response model."""
    status: str
    timestamp: str
    ocr_server_url: str
    supported_formats: List[str]
    max_file_size: int

class FastAPIOCRServer:
    """FastAPI server for OCR file processing."""
    
    def __init__(self, ocr_server_url: str = "http://localhost:8003", validate_files: bool = True):
        """
        Initialize the FastAPI OCR server.
        
        Args:
            ocr_server_url: URL of the A2A OCR agent server
            validate_files: Whether to validate uploaded files
        """
        self.ocr_server_url = ocr_server_url
        self.validate_files = validate_files
        self.app = FastAPI(
            title="A2A OCR API Server",
            description="HTTP API server for OCR processing using A2A protocol",
            version="1.0.0",
            docs_url="/docs",
            redoc_url="/redoc"
        )
        
        # Add CORS middleware
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        self.setup_routes()
        
    def setup_routes(self):
        """Setup API routes."""
        
        @self.app.get("/", response_model=Dict[str, str])
        async def root():
            """Root endpoint with API information."""
            return {
                "message": "A2A OCR API Server",
                "version": "1.0.0",
                "docs": "/docs",
                "health": "/health",
                "upload": "/upload"
            }
        
        @self.app.get("/health", response_model=HealthResponse)
        async def health_check():
            """Health check endpoint."""
            return HealthResponse(
                status="healthy",
                timestamp=time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
                ocr_server_url=self.ocr_server_url,
                supported_formats=list(SUPPORTED_IMAGE_FORMATS.keys()),
                max_file_size=MAX_FILE_SIZE
            )
        
        @self.app.post("/upload", response_model=OCRResponse)
        async def upload_files(
            files: List[UploadFile] = File(..., description="Image files to process"),
            user_id: Optional[str] = Form(None, description="Optional user ID"),
            context_id: Optional[str] = Form(None, description="Optional context ID for conversation continuity"),
            description: Optional[str] = Form(None, description="Optional description for the processing task"),
            include_file_data: bool = Form(False, description="Whether to include base64-encoded file data")
        ):
            """
            Upload and process multiple image files for OCR.
            
            This endpoint accepts multiple image files via multipart/form-data and forwards them
            to the A2A OCR agent for text extraction and analysis.
            
            Supported formats: JPG, JPEG, PNG, PDF, TIFF, TIF, BMP, GIF, WEBP, SVG
            Maximum file size: 10MB per file
            """
            start_time = time.time()
            task_id = str(uuid4())
            user_id = user_id or f"api_user_{int(time.time())}"
            
            logger.info(f"Processing upload request - Task ID: {task_id}, User: {user_id}, Files: {len(files)}")
            
            if not files:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No files provided"
                )
            
            # Validate and process files
            temp_files = []
            processed_files = []
            
            try:
                for i, file in enumerate(files):
                    # Validate file
                    if not file.filename:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"File {i+1} has no filename"
                        )
                    
                    # Check file extension
                    file_ext = Path(file.filename).suffix.lower()
                    if file_ext not in SUPPORTED_IMAGE_FORMATS:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Unsupported file format: {file_ext}. Supported: {list(SUPPORTED_IMAGE_FORMATS.keys())}"
                        )
                    
                    # Read file content
                    file_content = await file.read()
                    
                    # Check file size
                    if len(file_content) > MAX_FILE_SIZE:
                        raise HTTPException(
                            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                            detail=f"File {file.filename} is too large: {len(file_content)} bytes. Maximum: {MAX_FILE_SIZE} bytes"
                        )
                    
                    # Save to temporary file
                    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=file_ext)
                    temp_file.write(file_content)
                    temp_file.close()
                    
                    temp_files.append(temp_file.name)
                    processed_files.append({
                        'path': temp_file.name,
                        'name': Path(file.filename).stem,
                        'original_filename': file.filename,
                        'size': len(file_content),
                        'mime_type': SUPPORTED_IMAGE_FORMATS.get(file_ext, 'application/octet-stream')
                    })
                    
                    logger.debug(f"Processed file {i+1}: {file.filename} ({len(file_content)} bytes)")
                
                # Forward to A2A OCR agent
                async with A2AOCRClient(server_url=self.ocr_server_url, validate_files=self.validate_files) as client:
                    result = await client.process_images(
                        processed_files, 
                        context_id=context_id,
                        include_file_data=include_file_data
                    )
                
                processing_time = time.time() - start_time
                
                logger.info(f"OCR processing completed - Task ID: {task_id}, Time: {processing_time:.2f}s")
                
                return OCRResponse(
                    status="success",
                    task_id=task_id,
                    user_id=user_id,
                    context_id=context_id,
                    processing_time=processing_time,
                    file_count=len(files),
                    results=result
                )
                
            except HTTPException:
                # Re-raise HTTP exceptions
                raise
            except Exception as e:
                logger.error(f"OCR processing failed - Task ID: {task_id}: {e}")
                processing_time = time.time() - start_time
                
                return OCRResponse(
                    status="error",
                    task_id=task_id,
                    user_id=user_id,
                    context_id=context_id,
                    processing_time=processing_time,
                    file_count=len(files),
                    results={},
                    error=str(e)
                )
            
            finally:
                # Clean up temporary files
                for temp_file in temp_files:
                    try:
                        Path(temp_file).unlink()
                    except Exception as e:
                        logger.warning(f"Failed to delete temporary file {temp_file}: {e}")

def create_app(ocr_server_url: str = "http://localhost:8003", validate_files: bool = True) -> FastAPI:
    """Create and configure the FastAPI application."""
    server = FastAPIOCRServer(ocr_server_url=ocr_server_url, validate_files=validate_files)
    return server.app

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="FastAPI OCR Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8005, help="Port to bind to")
    parser.add_argument("--ocr-server", default="http://localhost:8003", help="A2A OCR agent server URL")
    parser.add_argument("--no-validate", action="store_true", help="Disable file validation")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload for development")
    parser.add_argument("--log-level", default="info", choices=["debug", "info", "warning", "error"], help="Log level")
    
    args = parser.parse_args()
    
    # Configure logging level
    logging.getLogger().setLevel(getattr(logging, args.log_level.upper()))
    
    # Create the app
    app = create_app(ocr_server_url=args.ocr_server, validate_files=not args.no_validate)
    
    logger.info(f"Starting FastAPI OCR Server on {args.host}:{args.port}")
    logger.info(f"OCR Agent URL: {args.ocr_server}")
    logger.info(f"API Documentation: http://{args.host}:{args.port}/docs")
    logger.info(f"File validation: {'disabled' if args.no_validate else 'enabled'}")
    
    # Run the server
    uvicorn.run(
        app,
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level=args.log_level
    )

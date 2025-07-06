#!/usr/bin/env python3
"""
Enhanced A2A OCR Client

A comprehensive Python client using the python-a2a library to communicate with the A2A OCR agent server.
This client can send multiple image files to the OCR agent for text extraction and analysis.

Features:
- Support for multiple image formats (JPG, PNG, PDF, TIFF, BMP, GIF, WEBP)
- File validation and error handling
- Base64 encoding for file transmission
- Batch processing with progress tracking
- Comprehensive logging and debugging

Usage:
    python a2a_ocr_client.py --images image1.jpg image2.png --server http://localhost:8003
    python a2a_ocr_client.py --directory ./images --server http://localhost:8003
"""

import asyncio
import base64
import json
import logging
import mimetypes
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from uuid import uuid4

import click
import httpx

# A2A client imports
from a2a.client import A2AClient, create_text_message_object
from a2a.types import (
    MessageSendConfiguration,
    MessageSendParams,
    SendMessageRequest,
    SendMessageResponse,
    SendMessageSuccessResponse,
)

# Import file utilities
from file_utils import FileProcessor, FileValidationError, SUPPORTED_IMAGE_FORMATS, MAX_FILE_SIZE

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# File validation settings (imported from file_utils)
VALIDATE_FILES = True


class A2AOCRClient:
    """Enhanced A2A client for communicating with the OCR agent server."""

    def __init__(self, server_url: str = "http://localhost:8003", timeout: int = 60, validate_files: bool = True):
        """
        Initialize the A2A OCR client.

        Args:
            server_url: Base URL of the OCR agent server
            timeout: Request timeout in seconds
            validate_files: Whether to validate files before processing
        """
        self.server_url = server_url.rstrip('/')
        self.timeout = timeout
        self.validate_files = validate_files
        self.httpx_client: Optional[httpx.AsyncClient] = None
        self.a2a_client: Optional[A2AClient] = None
        self.file_processor = FileProcessor(validate_signatures=validate_files)
        
    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()
        
    async def connect(self) -> None:
        """Connect to the OCR agent server."""
        try:
            logger.info(f"Connecting to OCR agent at {self.server_url}")

            # Create HTTP client
            self.httpx_client = httpx.AsyncClient(timeout=self.timeout)

            # The OCR agent uses a custom RPC endpoint at /a2a/ocr_agent
            # We need to specify this directly since it's not in the agent card
            rpc_endpoint_url = f"{self.server_url}/a2a/ocr_agent"

            # Create A2A client with direct RPC endpoint URL
            self.a2a_client = A2AClient(
                httpx_client=self.httpx_client,
                url=rpc_endpoint_url
            )

            logger.info(f"Successfully connected to OCR agent RPC endpoint: {rpc_endpoint_url}")

        except Exception as e:
            logger.error(f"Failed to connect to OCR agent: {e}")
            if self.httpx_client:
                await self.httpx_client.aclose()
            raise
            
    async def disconnect(self) -> None:
        """Disconnect from the OCR agent server."""
        if self.httpx_client:
            await self.httpx_client.aclose()
            logger.info("Disconnected from OCR agent")

    def validate_file(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Validate a single file for OCR processing.

        Args:
            file_path: Path to the file to validate

        Returns:
            Dict containing validation results and file metadata

        Raises:
            ValueError: If file validation fails
        """
        try:
            return self.file_processor.validate_file(file_path)
        except FileValidationError as e:
            raise ValueError(str(e))

    def discover_images_in_directory(self, directory: Union[str, Path], recursive: bool = False) -> List[Path]:
        """
        Discover image files in a directory.

        Args:
            directory: Directory path to search
            recursive: Whether to search recursively

        Returns:
            List of image file paths
        """
        try:
            file_infos = self.file_processor.discover_images_in_directory(
                directory, recursive, validate=False
            )
            return [Path(info['path']) for info in file_infos]
        except FileValidationError as e:
            raise ValueError(str(e))
            
    async def process_images(
        self,
        images: List[Union[str, Path, Dict[str, Any]]],
        context_id: Optional[str] = None,
        include_file_data: bool = False
    ) -> Dict[str, Any]:
        """
        Send multiple images to the OCR agent for processing.

        Args:
            images: List of image paths (strings/Path objects) or image objects (dicts)
            context_id: Optional context ID for conversation continuity
            include_file_data: Whether to include base64-encoded file data

        Returns:
            Dict containing the OCR processing results

        Raises:
            ValueError: If no images provided or client not connected
            Exception: If the request fails
        """
        if not images:
            raise ValueError("No images provided for processing")

        if not self.a2a_client:
            raise ValueError("Client not connected. Use async context manager or call connect() first")

        # Validate and format images for the OCR agent
        formatted_images = await self._format_and_validate_images(images, include_file_data)

        # Create the message content as JSON string (as expected by the OCR agent)
        message_content = json.dumps(formatted_images)

        logger.info(f"Sending {len(formatted_images)} images for OCR processing")
        logger.debug(f"Message content preview: {message_content[:200]}...")

        try:
            # Create the A2A message
            message = create_text_message_object(content=message_content)
            if context_id:
                message.contextId = context_id

            # Create message send parameters
            params = MessageSendParams(
                message=message,
                configuration=MessageSendConfiguration(
                    acceptedOutputModes=["text"],
                    blocking=True
                )
            )

            # Create and send the request
            request = SendMessageRequest(
                id=str(uuid4()),
                params=params
            )

            response: SendMessageResponse = await self.a2a_client.send_message(request)

            # Process the response
            return self._process_response(response)

        except Exception as e:
            logger.error(f"Failed to process images: {e}")
            raise
            
    async def _format_and_validate_images(
        self,
        images: List[Union[str, Path, Dict[str, Any]]],
        include_file_data: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Format and validate images for the OCR agent.

        Args:
            images: List of image paths or image objects
            include_file_data: Whether to include base64-encoded file data

        Returns:
            List of formatted and validated image objects
        """
        formatted_images = []

        for i, image in enumerate(images):
            try:
                if isinstance(image, (str, Path)):
                    # Path-based image
                    image_path = Path(image)

                    # Validate file if validation is enabled
                    if self.validate_files:
                        file_info = self.validate_file(image_path)
                    else:
                        file_info = {
                            'path': str(image_path),
                            'name': image_path.stem,
                            'size': image_path.stat().st_size if image_path.exists() else 0,
                            'mime_type': SUPPORTED_IMAGE_FORMATS.get(image_path.suffix.lower(), 'application/octet-stream')
                        }

                    formatted_image = {
                        'path': file_info['path'],
                        'name': file_info['name'] or f"Image_{i+1}",
                        'description': f"Image file: {image_path.name}",
                        'size': file_info['size'],
                        'mime_type': file_info['mime_type'],
                        'index': i
                    }

                    # Include file data if requested
                    if include_file_data and image_path.exists():
                        with open(image_path, 'rb') as f:
                            file_data = f.read()
                            formatted_image['data'] = base64.b64encode(file_data).decode('utf-8')

                elif isinstance(image, dict):
                    # Image object with metadata
                    image_path = image.get('path') or image.get('file')
                    if image_path:
                        image_path = Path(image_path)
                        if self.validate_files and image_path.exists():
                            file_info = self.validate_file(image_path)
                        else:
                            file_info = {'path': str(image_path), 'name': image_path.stem, 'size': 0}
                    else:
                        file_info = {'path': f'image_{i}', 'name': f'Image_{i+1}', 'size': 0}

                    formatted_image = {
                        'path': file_info['path'],
                        'name': image.get('name') or file_info['name'] or f"Image_{i+1}",
                        'description': image.get('description') or f"Image file: {Path(file_info['path']).name}",
                        'size': file_info.get('size', 0),
                        'mime_type': image.get('mime_type') or file_info.get('mime_type', 'application/octet-stream'),
                        'index': i
                    }

                    # Include existing data or load from file
                    if include_file_data:
                        if 'data' in image:
                            formatted_image['data'] = image['data']
                        elif image_path and image_path.exists():
                            with open(image_path, 'rb') as f:
                                file_data = f.read()
                                formatted_image['data'] = base64.b64encode(file_data).decode('utf-8')

                else:
                    # Fallback for other types
                    formatted_image = {
                        'path': str(image),
                        'name': f"Image_{i+1}",
                        'description': "Image for OCR processing",
                        'size': 0,
                        'mime_type': 'application/octet-stream',
                        'index': i
                    }

                formatted_images.append(formatted_image)
                logger.debug(f"Formatted image {i+1}: {formatted_image['name']} ({formatted_image['size']} bytes)")

            except Exception as e:
                logger.error(f"Failed to process image {i+1}: {e}")
                if self.validate_files:
                    raise
                # Continue with basic info if validation is disabled
                formatted_images.append({
                    'path': str(image),
                    'name': f"Image_{i+1}",
                    'description': f"Image processing error: {e}",
                    'size': 0,
                    'mime_type': 'application/octet-stream',
                    'index': i,
                    'error': str(e)
                })

        return formatted_images
        
    def _process_response(self, response: SendMessageResponse) -> Dict[str, Any]:
        """
        Process the A2A response from the OCR agent.

        Args:
            response: The A2A response object

        Returns:
            Dict containing the processed response data
        """
        try:
            if isinstance(response.root, SendMessageSuccessResponse):
                # Extract the message content
                result = response.root.result

                # Handle different response structures
                response_text = None

                # Try to extract text from various possible structures
                if hasattr(result, 'parts') and result.parts:
                    # Check if parts exist and have text content
                    for part in result.parts:
                        if hasattr(part, 'text') and part.text:
                            response_text = part.text
                            break
                        elif hasattr(part, 'root'):
                            if hasattr(part.root, 'text') and part.root.text:
                                response_text = part.root.text
                                break
                            elif hasattr(part.root, 'content') and part.root.content:
                                response_text = part.root.content
                                break

                # If we found text content, try to parse it
                if response_text:
                    # Try to parse as JSON (OCR agent returns structured JSON)
                    try:
                        parsed_json = json.loads(response_text)
                        return {
                            'status': 'success',
                            'response_type': 'json',
                            'content': parsed_json
                        }
                    except json.JSONDecodeError:
                        # If not JSON, return as plain text
                        return {
                            'status': 'success',
                            'response_type': 'text',
                            'content': response_text
                        }

                # Fallback: try to extract any available content
                if hasattr(result, 'model_dump'):
                    result_dict = result.model_dump()
                    return {
                        'status': 'success',
                        'response_type': 'structured',
                        'content': result_dict
                    }
                else:
                    return {
                        'status': 'success',
                        'response_type': 'raw',
                        'content': str(result)
                    }
            else:
                # Error response
                return {
                    'status': 'error',
                    'error': str(response.root)
                }

        except Exception as e:
            logger.error(f"Failed to process response: {e}")
            logger.debug(f"Response object: {response}")
            return {
                'status': 'error',
                'error': f"Response processing failed: {e}",
                'raw_response': str(response) if response else None
            }


async def main_async(
    images: List[str],
    server: str,
    context_id: Optional[str] = None,
    output_file: Optional[str] = None,
    directory: Optional[str] = None,
    recursive: bool = False,
    include_file_data: bool = False
) -> None:
    """
    Main async function to process images using the A2A OCR client.

    Args:
        images: List of image file paths
        server: OCR agent server URL
        context_id: Optional context ID
        output_file: Optional output file path
        directory: Optional directory to scan for images
        recursive: Whether to scan directory recursively
        include_file_data: Whether to include base64-encoded file data
    """
    # Collect all image paths
    all_images: List[Union[str, Path]] = []

    # Add images from directory if specified
    if directory:
        try:
            client = A2AOCRClient(server_url=server)
            discovered_images = client.discover_images_in_directory(directory, recursive)
            all_images.extend(discovered_images)
            logger.info(f"Discovered {len(discovered_images)} images in directory: {directory}")
        except Exception as e:
            logger.error(f"Failed to scan directory {directory}: {e}")
            sys.exit(1)

    # Add individual image files
    for image_path in images:
        path_obj = Path(image_path)
        if not path_obj.exists():
            logger.error(f"Image file not found: {image_path}")
            sys.exit(1)
        all_images.append(path_obj)

    if not all_images:
        logger.error("No images provided for processing")
        sys.exit(1)

    logger.info(f"Processing {len(all_images)} images total")

    async with A2AOCRClient(server_url=server) as client:
        try:
            # Process the images
            result = await client.process_images(all_images, context_id=context_id, include_file_data=include_file_data)

            # Output results
            if output_file:
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(result, f, indent=2, ensure_ascii=False)
                logger.info(f"Results saved to: {output_file}")
            else:
                print(json.dumps(result, indent=2, ensure_ascii=False))

        except Exception as e:
            logger.error(f"OCR processing failed: {e}")
            sys.exit(1)


@click.command()
@click.option(
    '--images', '-i',
    multiple=True,
    help='Image file paths to process (can be specified multiple times)'
)
@click.option(
    '--directory', '-d',
    help='Directory to scan for image files'
)
@click.option(
    '--recursive', '-r',
    is_flag=True,
    help='Scan directory recursively for images'
)
@click.option(
    '--server', '-s',
    default='http://localhost:8003',
    help='OCR agent server URL (default: http://localhost:8003)'
)
@click.option(
    '--context-id', '-c',
    help='Optional context ID for conversation continuity'
)
@click.option(
    '--output', '-o',
    help='Output file path (if not specified, prints to stdout)'
)
@click.option(
    '--include-data',
    is_flag=True,
    help='Include base64-encoded file data in the request'
)
@click.option(
    '--no-validate',
    is_flag=True,
    help='Disable file validation'
)
@click.option(
    '--verbose', '-v',
    is_flag=True,
    help='Enable verbose logging'
)
def main(images, directory, recursive, server, context_id, output, include_data, no_validate, verbose):
    """Enhanced A2A OCR Client - Send images to OCR agent for text extraction and analysis.

    Examples:
        # Process specific images
        python a2a_ocr_client.py -i image1.jpg -i image2.png

        # Process all images in a directory
        python a2a_ocr_client.py -d ./images

        # Process directory recursively
        python a2a_ocr_client.py -d ./images -r

        # Save results to file
        python a2a_ocr_client.py -i image.jpg -o results.json
    """
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Validate arguments
    if not images and not directory:
        click.echo("Error: Must specify either --images or --directory", err=True)
        sys.exit(1)

    asyncio.run(main_async(
        list(images) if images else [],
        server,
        context_id,
        output,
        directory,
        recursive,
        include_data
    ))


if __name__ == '__main__':
    main()

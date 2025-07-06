#!/usr/bin/env python3
"""
File Utilities for A2A OCR System

Comprehensive file handling utilities for the A2A OCR client system.
Provides file validation, format detection, metadata extraction, and error handling.

Features:
- Support for multiple image formats (JPG, PNG, PDF, TIFF, BMP, GIF, WEBP, SVG)
- File validation and size checking
- MIME type detection
- Metadata extraction
- Batch file processing
- Error handling and logging
"""

import logging
import mimetypes
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
import hashlib
import time

# Configure logging
logger = logging.getLogger(__name__)

# Supported image formats and their MIME types
SUPPORTED_IMAGE_FORMATS = {
    '.jpg': 'image/jpeg',
    '.jpeg': 'image/jpeg',
    '.png': 'image/png',
    '.pdf': 'application/pdf',
    '.tiff': 'image/tiff',
    '.tif': 'image/tiff',
    '.bmp': 'image/bmp',
    '.gif': 'image/gif',
    '.webp': 'image/webp',
    '.svg': 'image/svg+xml',
}

# File size limits
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
MIN_FILE_SIZE = 100  # 100 bytes

# Common image file signatures (magic numbers)
IMAGE_SIGNATURES = {
    b'\xFF\xD8\xFF': 'image/jpeg',  # JPEG
    b'\x89PNG\r\n\x1a\n': 'image/png',  # PNG
    b'GIF87a': 'image/gif',  # GIF87a
    b'GIF89a': 'image/gif',  # GIF89a
    b'BM': 'image/bmp',  # BMP
    b'RIFF': 'image/webp',  # WEBP (needs additional check)
    b'%PDF': 'application/pdf',  # PDF
    b'II*\x00': 'image/tiff',  # TIFF (little endian)
    b'MM\x00*': 'image/tiff',  # TIFF (big endian)
}

class FileValidationError(Exception):
    """Custom exception for file validation errors."""
    pass

class FileProcessor:
    """Comprehensive file processing utility for OCR operations."""
    
    def __init__(self, 
                 max_file_size: int = MAX_FILE_SIZE,
                 min_file_size: int = MIN_FILE_SIZE,
                 validate_signatures: bool = True):
        """
        Initialize the file processor.
        
        Args:
            max_file_size: Maximum allowed file size in bytes
            min_file_size: Minimum allowed file size in bytes
            validate_signatures: Whether to validate file signatures
        """
        self.max_file_size = max_file_size
        self.min_file_size = min_file_size
        self.validate_signatures = validate_signatures
        
    def validate_file(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Validate a single file for OCR processing.
        
        Args:
            file_path: Path to the file to validate
            
        Returns:
            Dict containing validation results and file metadata
            
        Raises:
            FileValidationError: If file validation fails
        """
        file_path = Path(file_path)
        
        # Check if file exists
        if not file_path.exists():
            raise FileValidationError(f"File not found: {file_path}")
            
        # Check if it's a file (not directory)
        if not file_path.is_file():
            raise FileValidationError(f"Path is not a file: {file_path}")
            
        # Get file stats
        try:
            file_stats = file_path.stat()
            file_size = file_stats.st_size
            modified_time = file_stats.st_mtime
        except OSError as e:
            raise FileValidationError(f"Cannot access file {file_path}: {e}")
            
        # Check file size
        if file_size < self.min_file_size:
            raise FileValidationError(f"File too small: {file_size} bytes. Minimum: {self.min_file_size} bytes")
            
        if file_size > self.max_file_size:
            raise FileValidationError(f"File too large: {file_size} bytes. Maximum: {self.max_file_size} bytes")
            
        # Check file extension
        file_ext = file_path.suffix.lower()
        if file_ext not in SUPPORTED_IMAGE_FORMATS:
            raise FileValidationError(f"Unsupported file format: {file_ext}. Supported formats: {list(SUPPORTED_IMAGE_FORMATS.keys())}")
            
        # Get MIME type from extension
        mime_type = SUPPORTED_IMAGE_FORMATS.get(file_ext)
        
        # Validate file signature if enabled
        if self.validate_signatures:
            detected_mime = self._detect_file_type(file_path)
            if detected_mime and not self._mime_types_compatible(mime_type, detected_mime):
                logger.warning(f"File extension {file_ext} doesn't match detected type {detected_mime} for {file_path}")
                # Use detected type if it's supported
                if detected_mime in SUPPORTED_IMAGE_FORMATS.values():
                    mime_type = detected_mime
                    
        # Calculate file hash for integrity
        file_hash = self._calculate_file_hash(file_path)
        
        return {
            'path': str(file_path),
            'name': file_path.stem,
            'filename': file_path.name,
            'extension': file_ext,
            'size': file_size,
            'mime_type': mime_type,
            'hash': file_hash,
            'modified_time': modified_time,
            'is_valid': True
        }
        
    def _detect_file_type(self, file_path: Path) -> Optional[str]:
        """
        Detect file type by reading file signature.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Detected MIME type or None
        """
        try:
            with open(file_path, 'rb') as f:
                header = f.read(32)  # Read first 32 bytes
                
            for signature, mime_type in IMAGE_SIGNATURES.items():
                if header.startswith(signature):
                    # Special case for WEBP
                    if signature == b'RIFF' and len(header) >= 12:
                        if header[8:12] == b'WEBP':
                            return 'image/webp'
                        else:
                            continue
                    return mime_type
                    
        except Exception as e:
            logger.debug(f"Failed to detect file type for {file_path}: {e}")
            
        return None
        
    def _mime_types_compatible(self, expected: str, detected: str) -> bool:
        """
        Check if MIME types are compatible.
        
        Args:
            expected: Expected MIME type from file extension
            detected: Detected MIME type from file signature
            
        Returns:
            True if compatible, False otherwise
        """
        if expected == detected:
            return True
            
        # Handle JPEG variations
        if expected == 'image/jpeg' and detected == 'image/jpeg':
            return True
            
        # Handle TIFF variations
        if expected == 'image/tiff' and detected == 'image/tiff':
            return True
            
        return False
        
    def _calculate_file_hash(self, file_path: Path) -> str:
        """
        Calculate SHA-256 hash of the file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Hexadecimal hash string
        """
        try:
            hash_sha256 = hashlib.sha256()
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_sha256.update(chunk)
            return hash_sha256.hexdigest()
        except Exception as e:
            logger.debug(f"Failed to calculate hash for {file_path}: {e}")
            return ""
            
    def discover_images_in_directory(self, 
                                   directory: Union[str, Path], 
                                   recursive: bool = False,
                                   validate: bool = True) -> List[Dict[str, Any]]:
        """
        Discover and optionally validate image files in a directory.
        
        Args:
            directory: Directory path to search
            recursive: Whether to search recursively
            validate: Whether to validate discovered files
            
        Returns:
            List of file information dictionaries
        """
        directory = Path(directory)
        if not directory.exists() or not directory.is_dir():
            raise FileValidationError(f"Directory not found or not a directory: {directory}")
            
        image_files = []
        pattern = "**/*" if recursive else "*"
        
        for file_path in directory.glob(pattern):
            if file_path.is_file() and file_path.suffix.lower() in SUPPORTED_IMAGE_FORMATS:
                try:
                    if validate:
                        file_info = self.validate_file(file_path)
                    else:
                        file_info = {
                            'path': str(file_path),
                            'name': file_path.stem,
                            'filename': file_path.name,
                            'extension': file_path.suffix.lower(),
                            'size': file_path.stat().st_size,
                            'mime_type': SUPPORTED_IMAGE_FORMATS.get(file_path.suffix.lower()),
                            'is_valid': None  # Not validated
                        }
                    image_files.append(file_info)
                except FileValidationError as e:
                    logger.warning(f"Skipping invalid file {file_path}: {e}")
                    continue
                except Exception as e:
                    logger.error(f"Error processing file {file_path}: {e}")
                    continue
                    
        return sorted(image_files, key=lambda x: x['path'])
        
    def batch_validate_files(self, file_paths: List[Union[str, Path]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Validate multiple files in batch.
        
        Args:
            file_paths: List of file paths to validate
            
        Returns:
            Tuple of (valid_files, invalid_files) lists
        """
        valid_files = []
        invalid_files = []
        
        for file_path in file_paths:
            try:
                file_info = self.validate_file(file_path)
                valid_files.append(file_info)
            except FileValidationError as e:
                invalid_files.append({
                    'path': str(file_path),
                    'error': str(e),
                    'is_valid': False
                })
            except Exception as e:
                invalid_files.append({
                    'path': str(file_path),
                    'error': f"Unexpected error: {e}",
                    'is_valid': False
                })
                
        return valid_files, invalid_files
        
    def get_file_summary(self, file_infos: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate a summary of file information.
        
        Args:
            file_infos: List of file information dictionaries
            
        Returns:
            Summary dictionary
        """
        if not file_infos:
            return {
                'total_files': 0,
                'total_size': 0,
                'formats': {},
                'valid_files': 0,
                'invalid_files': 0
            }
            
        total_size = sum(info.get('size', 0) for info in file_infos)
        formats = {}
        valid_count = 0
        invalid_count = 0
        
        for info in file_infos:
            # Count formats
            ext = info.get('extension', 'unknown')
            formats[ext] = formats.get(ext, 0) + 1
            
            # Count valid/invalid
            if info.get('is_valid') is True:
                valid_count += 1
            elif info.get('is_valid') is False:
                invalid_count += 1
                
        return {
            'total_files': len(file_infos),
            'total_size': total_size,
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'formats': formats,
            'valid_files': valid_count,
            'invalid_files': invalid_count,
            'largest_file': max(file_infos, key=lambda x: x.get('size', 0)) if file_infos else None,
            'smallest_file': min(file_infos, key=lambda x: x.get('size', 0)) if file_infos else None
        }

# Convenience functions
def validate_file(file_path: Union[str, Path], **kwargs) -> Dict[str, Any]:
    """Convenience function to validate a single file."""
    processor = FileProcessor(**kwargs)
    return processor.validate_file(file_path)

def discover_images(directory: Union[str, Path], recursive: bool = False, **kwargs) -> List[Dict[str, Any]]:
    """Convenience function to discover images in a directory."""
    processor = FileProcessor(**kwargs)
    return processor.discover_images_in_directory(directory, recursive, validate=True)

def batch_validate(file_paths: List[Union[str, Path]], **kwargs) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Convenience function to validate multiple files."""
    processor = FileProcessor(**kwargs)
    return processor.batch_validate_files(file_paths)

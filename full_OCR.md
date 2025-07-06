# Complete A2A OCR System Technical Documentation

## Table of Contents
1. [System Architecture](#system-architecture)
2. [Core Components](#core-components)
3. [Technical Requirements](#technical-requirements)
4. [Communication Protocols](#communication-protocols)
5. [Operational Workflows](#operational-workflows)
6. [Testing and Validation](#testing-and-validation)
7. [Troubleshooting Guide](#troubleshooting-guide)
8. [API Reference](#api-reference)

## System Architecture

### Overview
The A2A OCR System implements a sophisticated two-layer architecture designed to bridge HTTP-based file uploads with Agent-to-Agent (A2A) protocol communication for OCR processing.

### Architecture Diagram
```
┌─────────────────┐    HTTP/multipart     ┌─────────────────┐
│   HTTP Client   │ ────────────────────► │  FastAPI Server │
│   (Postman)     │    form-data          │    (Layer 1)    │
└─────────────────┘                       └─────────────────┘
                                                    │
                                                    │ A2A Protocol
                                                    ▼
                                          ┌─────────────────┐
                                          │  A2A OCR Client │
                                          │    (Layer 2)    │
                                          └─────────────────┘
                                                    │
                                                    │ JSON-RPC
                                                    ▼
                                          ┌─────────────────┐
                                          │ OCR Agent Server│
                                          │   (MCP Tool)    │
                                          └─────────────────┘
```

### Component Relationships

#### Layer 1: HTTP API Server
- **Purpose**: Accept HTTP file uploads and provide RESTful API interface
- **Technology**: FastAPI with async/await support
- **Responsibilities**:
  - File validation and format checking
  - Multipart form-data parsing
  - Request routing and response formatting
  - Error handling and logging

#### Layer 2: A2A OCR Client
- **Purpose**: Bridge HTTP requests to A2A protocol communication
- **Technology**: python-a2a library with httpx client
- **Responsibilities**:
  - A2A protocol implementation
  - Agent discovery and connection management
  - File encoding and transmission
  - Response processing and formatting

#### OCR Agent Server
- **Purpose**: Process images using OCR capabilities
- **Technology**: Google ADK with MCP tool integration
- **Responsibilities**:
  - Image processing and text extraction
  - MCP OCR tool orchestration
  - Result formatting and metadata generation
  - Session and context management

### Data Flow

1. **HTTP Request**: Client uploads files via multipart/form-data
2. **File Processing**: FastAPI server validates and processes files
3. **A2A Communication**: Files forwarded to A2A client
4. **Agent Discovery**: A2A client discovers OCR agent endpoints
5. **OCR Processing**: Agent processes images using MCP OCR tool
6. **Response Chain**: Results flow back through the layers
7. **HTTP Response**: Formatted JSON response to client

## Core Components

### 1. OCR Agent Server (`Multi_agent_mcp/ocr_agent/`)

#### Agent Configuration (`agent.py`)
```python
def create_ocr_agent() -> Agent:
    return Agent(
        name="ocr_agent",
        model="gemini-2.0-flash",
        description="Agent that processes images and extracts content using OCR capabilities.",
        instruction=OCR_PROMPT,
        tools=[
            MCPToolset(
                connection_params=StdioServerParameters(
                    command="python",
                    args=["-m", "mcp_ocr"],
                    env={}
                )
            ),
        ],
    )
```

#### Server Startup (`_main_.py`)
- **Port Configuration**: Default port 8003
- **Endpoint Structure**:
  - Agent Card: `/.well-known/agent.json`
  - RPC Endpoint: `/a2a/ocr_agent`
  - Extended Card: `/agent/authenticatedExtendedCard`

#### Agent Executor (`agent_executor.py`)
- **Input Processing**: Handles JSON image arrays and text inputs
- **Session Management**: Creates and manages ADK sessions
- **Response Formatting**: Structures OCR results with metadata
- **Error Handling**: Comprehensive error management with fallbacks

#### Agent Capabilities
```json
{
  "name": "OCR Image Processing Agent",
  "description": "Processes arrays of images using OCR capabilities",
  "capabilities": {
    "streaming": false,
    "pushNotifications": false
  },
  "defaultInputModes": ["text", "image"],
  "defaultOutputModes": ["text"],
  "skills": [{
    "id": "image_ocr_processing",
    "name": "Process images with OCR",
    "description": "Takes an array of images and extracts text content using OCR"
  }]
}
```

### 2. A2A OCR Client (`a2a_ocr_client.py`)

#### Connection Management
```python
async def connect(self) -> None:
    """Connect to the OCR agent server."""
    # Create HTTP client
    self.httpx_client = httpx.AsyncClient(timeout=self.timeout)
    
    # Direct RPC endpoint URL (critical fix for connection issues)
    rpc_endpoint_url = f"{self.server_url}/a2a/ocr_agent"
    
    # Create A2A client with direct RPC endpoint URL
    self.a2a_client = A2AClient(
        httpx_client=self.httpx_client,
        url=rpc_endpoint_url
    )
```

#### Image Processing Workflow
1. **File Validation**: Format and size checking
2. **Base64 Encoding**: Convert images to base64 for transmission
3. **Metadata Extraction**: Generate file metadata and descriptions
4. **A2A Communication**: Send structured requests to agent
5. **Response Processing**: Parse and format agent responses

#### CLI Interface
```bash
# Single image processing
python a2a_ocr_client.py -i image.jpg

# Multiple images
python a2a_ocr_client.py -i image1.jpg -i image2.png

# Directory processing
python a2a_ocr_client.py -d ./images --recursive

# Custom server URL
python a2a_ocr_client.py -i image.jpg -s http://localhost:8003
```

### 3. FastAPI HTTP Server (`fastapi_ocr_server.py`)

#### Server Configuration
```python
class FastAPIOCRServer:
    def __init__(self, ocr_server_url: str = "http://localhost:8003", validate_files: bool = True):
        self.app = FastAPI(
            title="A2A OCR API Server",
            description="HTTP API server for OCR processing using A2A protocol",
            version="1.0.0"
        )
```

#### File Upload Endpoint
```python
@app.post("/upload")
async def upload_files(
    files: List[UploadFile] = File(...),
    user_id: Optional[str] = Form(None),
    context_id: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    include_file_data: bool = Form(False)
):
```

#### Supported File Formats
- **Images**: JPG, JPEG, PNG, BMP, GIF, WEBP, TIFF
- **Documents**: PDF
- **Vector Graphics**: SVG
- **Validation**: Magic number verification and MIME type checking

### 4. File Processing Utilities (`file_utils.py`)

#### FileProcessor Class
```python
class FileProcessor:
    def __init__(self, 
                 max_file_size: int = 10 * 1024 * 1024,  # 10MB
                 validate_signatures: bool = True,
                 supported_formats: Optional[Dict[str, str]] = None):
```

#### Validation Features
- **Magic Number Validation**: Verify file signatures
- **Size Limits**: Configurable file size restrictions
- **Format Detection**: MIME type and extension validation
- **Metadata Extraction**: File properties and statistics
- **Batch Processing**: Handle multiple files efficiently

## Technical Requirements

### Python Dependencies

#### Core Requirements (`requirements.txt`)
```
fastapi>=0.104.1
uvicorn[standard]>=0.24.0
python-multipart>=0.0.6
httpx>=0.25.0
python-a2a>=0.1.0
Pillow>=10.0.0
pydantic>=2.0.0
click>=8.1.0
```

#### MCP OCR Tool Requirements
```
mcp-ocr>=1.10.1
pytesseract>=0.3.10
tesseract-ocr  # System dependency
```

#### Google ADK Requirements
```
google-adk>=1.0.0
google-genai>=0.3.0
litellm>=1.0.0
```

### System Dependencies

#### Tesseract OCR Installation

**Windows:**
```bash
# Using winget
winget install UB-Mannheim.TesseractOCR

# Using chocolatey
choco install tesseract

# Manual installation
# Download from: https://github.com/UB-Mannheim/tesseract/wiki
```

**Linux:**
```bash
# Ubuntu/Debian
sudo apt-get install tesseract-ocr

# CentOS/RHEL
sudo yum install tesseract

# Arch Linux
sudo pacman -S tesseract
```

**macOS:**
```bash
# Using Homebrew
brew install tesseract
```

### Environment Configuration

#### Required Environment Variables
```bash
# Server Configuration
export OCR_SERVER_URL="http://localhost:8003"
export API_SERVER_PORT="8005"
export API_SERVER_HOST="0.0.0.0"

# File Processing
export MAX_FILE_SIZE="10485760"  # 10MB
export VALIDATE_FILES="true"

# Logging
export LOG_LEVEL="INFO"

# Tesseract Configuration
export TESSDATA_PREFIX="/usr/share/tesseract-ocr/4.00/tessdata"
```

## Communication Protocols

### A2A Protocol Implementation

#### Agent Discovery
1. **Agent Card Retrieval**: GET `/.well-known/agent.json`
2. **Capability Verification**: Parse agent capabilities and skills
3. **Endpoint Resolution**: Identify RPC endpoint URL

#### JSON-RPC Message Structure
```json
{
  "jsonrpc": "2.0",
  "id": "unique-request-id",
  "method": "send_message",
  "params": {
    "message": {
      "content": [
        {
          "type": "text",
          "text": "JSON array of image data"
        }
      ],
      "role": "user"
    }
  }
}
```

#### Image Data Format
```json
[
  {
    "path": "temp_file_path",
    "name": "image_name",
    "description": "Image description",
    "size": 12345,
    "mime_type": "image/jpeg",
    "data": "base64_encoded_image_data"
  }
]
```

### MCP Protocol Integration

#### Tool Invocation
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "perform_ocr",
    "arguments": {
      "image_input": "base64_encoded_image"
    }
  }
}
```

#### Available MCP Tools
- **perform_ocr**: Extract text from images
- **get_supported_languages**: List available OCR languages

### Error Handling Mechanisms

#### Connection Error Recovery
```python
async def connect_with_retry(self, max_retries: int = 3) -> bool:
    for attempt in range(max_retries):
        try:
            await self.connect()
            return True
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            await asyncio.sleep(2 ** attempt)  # Exponential backoff
    return False
```

#### Fallback Strategies
1. **MCP Tool Failure**: Fall back to direct OCR implementation
2. **Connection Issues**: Retry with exponential backoff
3. **Agent Unavailable**: Return structured error response
4. **File Processing Errors**: Skip invalid files, process valid ones

## Operational Workflows

### Deployment Process

#### 1. Environment Setup
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements_fastapi_server.txt
pip install -r requirements_a2a_client.txt
```

#### 2. Tesseract Installation
```bash
# Run installation script (Windows)
./install_tesseract.bat

# Verify installation
tesseract --version
python -c "import pytesseract; print(pytesseract.get_tesseract_version())"
```

#### 3. Server Startup Sequence
```bash
# Terminal 1: Start OCR Agent Server
cd Multi_agent_mcp/ocr_agent
python _main_.py --host localhost --port 8003

# Terminal 2: Start FastAPI Server
cd Multi_agent_mcp
python fastapi_ocr_server.py --host 0.0.0.0 --port 8005

# Terminal 3: Test A2A Client
python a2a_ocr_client.py -i test_image.jpg
```

### Health Checking

#### Agent Server Health
```bash
# Check agent card availability
curl http://localhost:8003/.well-known/agent.json

# Test RPC endpoint
curl -X POST http://localhost:8003/a2a/ocr_agent \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"send_message","params":{"message":{"content":[{"type":"text","text":"test"}],"role":"user"}}}'
```

#### FastAPI Server Health
```bash
# Health check endpoint
curl http://localhost:8005/health

# API documentation
curl http://localhost:8005/docs
```

### Client Usage Scenarios

#### Scenario 1: Single Image Processing
```bash
python a2a_ocr_client.py -i document.jpg --verbose
```

#### Scenario 2: Batch Processing
```bash
python a2a_ocr_client.py -d ./documents --recursive --output results.json
```

#### Scenario 3: HTTP API Usage
```bash
curl -X POST "http://localhost:8005/upload" \
  -F "files=@document1.jpg" \
  -F "files=@document2.png" \
  -F "user_id=test_user" \
  -F "description=Batch OCR processing"
```

## Testing and Validation

### Unit Testing Approach

#### Component Testing
```python
# Test file validation
def test_file_validation():
    processor = FileProcessor()
    result = processor.validate_file("test_image.jpg")
    assert result['valid'] == True

# Test A2A connection
async def test_a2a_connection():
    async with A2AOCRClient() as client:
        assert client.a2a_client is not None
```

#### Integration Testing
```python
# Test end-to-end workflow
async def test_ocr_workflow():
    async with A2AOCRClient() as client:
        result = await client.process_images(["test_image.jpg"])
        assert result['status'] == 'success'
```

### Performance Testing

#### Load Testing
```python
import asyncio
import time

async def performance_test():
    start_time = time.time()
    tasks = []
    
    for i in range(10):  # Process 10 images concurrently
        task = process_single_image(f"test_image_{i}.jpg")
        tasks.append(task)
    
    results = await asyncio.gather(*tasks)
    end_time = time.time()
    
    print(f"Processed {len(results)} images in {end_time - start_time:.2f} seconds")
```

### Diagnostic Tools

#### System Diagnostic Script
```bash
python diagnose_ocr_issues.py
```

**Diagnostic Checks:**
- Python environment and packages
- Tesseract OCR installation
- MCP OCR tool functionality
- A2A connection status
- Agent server availability

#### Quick Fix Script
```bash
python fix_ocr_connection.py
```

**Automated Fixes:**
- Install missing packages
- Configure Tesseract OCR
- Create fallback agent configuration
- Update server configuration

## Troubleshooting Guide

### Common Issues and Solutions

#### 1. "Connection closed" Error

**Symptoms:**
```
Error processing images with OCR: Connection closed
```

**Root Causes:**
- Tesseract OCR not installed
- MCP tool configuration issues
- Environment variable problems

**Solutions:**
1. Install Tesseract OCR:
   ```bash
   winget install UB-Mannheim.TesseractOCR
   ```

2. Verify MCP tool:
   ```bash
   python -m mcp_ocr --help
   ```

3. Use direct OCR fallback:
   ```python
   from ocr_agent.direct_ocr_agent import create_direct_ocr_agent
   ```

#### 2. Agent Card Not Found (404 Error)

**Symptoms:**
```
HTTP Error 404: Client error '404 Not Found' for url 'http://localhost:8003/.well-known/agent.json'
```

**Solutions:**
1. Verify agent server is running:
   ```bash
   curl http://localhost:8003/.well-known/agent.json
   ```

2. Check server startup logs
3. Restart agent server with correct configuration

#### 3. RPC Endpoint Resolution Issues

**Symptoms:**
```
HTTP Error 404: Client error '404 Not Found' for url 'http://localhost:8003/'
```

**Solutions:**
1. Use direct RPC endpoint URL:
   ```python
   rpc_endpoint_url = f"{self.server_url}/a2a/ocr_agent"
   self.a2a_client = A2AClient(url=rpc_endpoint_url)
   ```

2. Verify endpoint configuration in agent server

#### 4. File Upload Issues

**Symptoms:**
- File validation errors
- Unsupported format messages
- Size limit exceeded

**Solutions:**
1. Check supported formats:
   ```python
   SUPPORTED_IMAGE_FORMATS = {
       '.jpg': 'image/jpeg',
       '.jpeg': 'image/jpeg',
       '.png': 'image/png',
       # ... more formats
   }
   ```

2. Adjust file size limits:
   ```python
   MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
   ```

### Debug Mode Configuration

#### Enable Verbose Logging
```python
import logging
logging.basicConfig(level=logging.DEBUG)

# For A2A client
python a2a_ocr_client.py -i image.jpg --verbose

# For FastAPI server
uvicorn fastapi_ocr_server:app --log-level debug
```

#### Network Debugging
```bash
# Monitor HTTP traffic
curl -v http://localhost:8003/.well-known/agent.json

# Test RPC endpoint
curl -X POST http://localhost:8003/a2a/ocr_agent \
  -H "Content-Type: application/json" \
  -d '{"test": "data"}' -v
```

## API Reference

### FastAPI Endpoints

#### POST /upload
Upload files for OCR processing.

**Request:**
```http
POST /upload
Content-Type: multipart/form-data

files: [file1.jpg, file2.png, ...]
user_id: optional_user_id
context_id: optional_context_id
description: optional_description
include_file_data: false
```

**Response:**
```json
{
  "status": "success",
  "task_id": "uuid",
  "processing_time": 2.34,
  "files_processed": 2,
  "results": [
    {
      "id": "uuid",
      "original_name": "document",
      "updated_name": "Invoice Document",
      "ocr_text": "Extracted text content...",
      "analysis": "Document analysis..."
    }
  ]
}
```

#### GET /health
Check server health status.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-07-06T12:00:00Z",
  "ocr_server_url": "http://localhost:8003",
  "version": "1.0.0"
}
```

### A2A Client API

#### Class: A2AOCRClient

**Constructor:**
```python
A2AOCRClient(
    server_url: str = "http://localhost:8003",
    timeout: int = 60,
    validate_files: bool = True
)
```

**Methods:**

##### process_images()
```python
async def process_images(
    self,
    image_paths: List[Union[str, Dict[str, Any]]],
    context_id: Optional[str] = None,
    include_file_data: bool = False
) -> Dict[str, Any]:
```

##### connect()
```python
async def connect(self) -> None:
```

##### disconnect()
```python
async def disconnect(self) -> None:
```

### File Processor API

#### Class: FileProcessor

**Constructor:**
```python
FileProcessor(
    max_file_size: int = 10 * 1024 * 1024,
    validate_signatures: bool = True,
    supported_formats: Optional[Dict[str, str]] = None
)
```

**Methods:**

##### validate_file()
```python
def validate_file(self, file_path: Union[str, Path]) -> Dict[str, Any]:
```

##### process_files()
```python
def process_files(self, file_paths: List[Union[str, Path]]) -> List[Dict[str, Any]]:
```

---

This comprehensive documentation provides complete technical coverage of the A2A OCR system, enabling both developers and operators to successfully implement, deploy, and maintain the system.

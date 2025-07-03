# Postman Testing Guide for OCR Agent

This guide provides step-by-step instructions for testing the modified OCR agent using Postman.

## Prerequisites

1. **OCR Agent Server Running**: Ensure the OCR agent server is running on `http://localhost:8003`
2. **Postman Installed**: Have Postman application or web version ready
3. **MCP OCR Tool**: Ensure `mcp_ocr` module is available in your Python environment

## Starting the OCR Agent Server

Before testing, start the OCR agent server:

```bash
cd Multi_agent_mcp/ocr_agent
python _main_.py --host localhost --port 8003
```

You should see output indicating the server is running.

## Test 1: Agent Card Verification

**Purpose**: Verify the agent is running and accessible.

### Request Configuration:
- **Method**: `GET`
- **URL**: `http://localhost:8003/.well-known/agent.json`
- **Headers**: None required

### Expected Response:
```json
{
  "name": "OCR Image Processing Agent",
  "description": "Processes arrays of images using OCR capabilities to extract text and provide detailed analysis.",
  "url": "http://localhost:8003/",
  "version": "1.0.0",
  "defaultInputModes": ["text", "image"],
  "defaultOutputModes": ["text"],
  "capabilities": {
    "streaming": false,
    "pushNotifications": false
  },
  "skills": [
    {
      "id": "image_ocr_processing",
      "name": "Process images with OCR",
      "description": "Takes an array of images and extracts text content using OCR, providing detailed analysis and updated metadata.",
      "tags": ["ocr", "image", "text-extraction", "analysis"],
      "examples": [
        "Process these document images for text extraction",
        "Analyze and extract content from multiple screenshots",
        "OCR processing for batch image analysis"
      ]
    }
  ]
}
```

## Test 2: Image Array Processing

**Purpose**: Test the main functionality with multiple images.

### Request Configuration:
- **Method**: `POST`
- **URL**: `http://localhost:8003/a2a/ocr_agent`
- **Headers**:
  ```
  Content-Type: application/json
  Accept: application/json
  ```

### Request Body:
```json
{
  "task_id": "test-task-001",
  "context_id": "test-context-001",
  "user_input": "[{\"path\": \"/path/to/invoice.jpg\", \"name\": \"Invoice Document\", \"description\": \"Company invoice for processing\"}, {\"path\": \"/path/to/screenshot.png\", \"name\": \"App Screenshot\", \"description\": \"Application interface screenshot\"}, \"/path/to/document.pdf\", {\"file\": \"/path/to/receipt.jpg\", \"name\": \"Receipt\", \"description\": \"Purchase receipt\"}]",
  "timestamp": 1704067200000
}
```

### Expected Response Structure:
```json
{
  "task_id": "test-task-001",
  "context_id": "test-context-001",
  "response": {
    "status": "success",
    "processed_images": 4,
    "results": [
      {
        "id": "unique-uuid-1",
        "original_name": "Invoice Document",
        "updated_name": "Updated name based on OCR",
        "original_description": "Company invoice for processing",
        "updated_description": "Updated description based on analysis",
        "ocr_text": "Extracted text content",
        "analysis": "Visual content analysis"
      }
      // ... more results for each image
    ]
  }
}
```

## Test 3: Single Text Input

**Purpose**: Test backward compatibility with plain text input.

### Request Configuration:
- **Method**: `POST`
- **URL**: `http://localhost:8003/a2a/ocr_agent`
- **Headers**:
  ```
  Content-Type: application/json
  Accept: application/json
  ```

### Request Body:
```json
{
  "task_id": "test-task-002",
  "context_id": "test-context-002",
  "user_input": "Please process this image for OCR analysis",
  "timestamp": 1704067200000
}
```

### Expected Response Structure:
```json
{
  "task_id": "test-task-002",
  "context_id": "test-context-002",
  "response": {
    "status": "success",
    "processed_images": 1,
    "results": [
      {
        "id": "unique-uuid",
        "original_name": "Text Input",
        "updated_name": "Processed Text",
        "original_description": "Text input for processing",
        "updated_description": "Text processing completed",
        "ocr_text": "Please process this image for OCR analysis",
        "analysis": "Text-based response processing"
      }
    ]
  }
}
```

## Test 4: Single Image Object

**Purpose**: Test processing of a single image object.

### Request Configuration:
- **Method**: `POST`
- **URL**: `http://localhost:8003/a2a/ocr_agent`
- **Headers**:
  ```
  Content-Type: application/json
  Accept: application/json
  ```

### Request Body:
```json
{
  "task_id": "test-task-003",
  "context_id": "test-context-003",
  "user_input": "{\"path\": \"/path/to/single_document.jpg\", \"name\": \"Single Document\", \"description\": \"A single document for OCR processing\"}",
  "timestamp": 1704067200000
}
```

## Test 5: Error Handling

**Purpose**: Test how the agent handles invalid input.

### Request Configuration:
- **Method**: `POST`
- **URL**: `http://localhost:8003/a2a/ocr_agent`
- **Headers**:
  ```
  Content-Type: application/json
  Accept: application/json
  ```

### Request Body (Invalid JSON):
```json
{
  "task_id": "test-task-004",
  "context_id": "test-context-004",
  "user_input": "invalid json [{ broken",
  "timestamp": 1704067200000
}
```

## Interpreting Results

### Success Indicators:
1. **HTTP Status 200**: Request was processed successfully
2. **Response Structure**: Contains `task_id`, `context_id`, and `response` fields
3. **Status Field**: `"status": "success"` in the response
4. **Unique IDs**: Each image result has a unique UUID in the `id` field
5. **Complete Results**: All required fields present in each result object

### Key Validation Points:
- ✅ **Unique ID Assignment**: Each image gets a different UUID
- ✅ **Image Count**: `processed_images` matches input array length
- ✅ **Metadata Enhancement**: `updated_name` and `updated_description` are different from originals
- ✅ **OCR Processing**: `ocr_text` field contains extracted content
- ✅ **Analysis**: `analysis` field provides visual content analysis

### Common Issues and Solutions:

1. **Connection Refused**: 
   - Ensure OCR agent server is running on port 8003
   - Check firewall settings

2. **500 Internal Server Error**:
   - Check server logs for MCP OCR tool issues
   - Verify `mcp_ocr` module is installed

3. **Empty or Malformed Response**:
   - Verify request body JSON format
   - Check `user_input` field is properly escaped JSON string

4. **Missing Fields in Response**:
   - Check agent logs for processing errors
   - Verify MCP OCR tool is functioning correctly

## Advanced Testing

### Custom Image Paths:
Replace the sample paths with actual image files on your system for real OCR testing.

### Batch Size Testing:
Test with different array sizes (1, 5, 10+ images) to verify scalability.

### Performance Testing:
Monitor response times for different batch sizes to ensure acceptable performance.

## Importing the Postman Collection

A ready-to-use Postman collection is provided: `OCR_Agent_Tests.postman_collection.json`

### Import Steps:
1. Open Postman
2. Click "Import" button
3. Select "Upload Files"
4. Choose `OCR_Agent_Tests.postman_collection.json`
5. Click "Import"

### Collection Features:
- ✅ Pre-configured requests for all test scenarios
- ✅ Automatic timestamp generation
- ✅ Response validation tests
- ✅ Environment variable for base URL
- ✅ Comprehensive error checking

### Running the Collection:
1. Select the imported "OCR Agent Tests" collection
2. Click "Run" to execute all tests
3. Review the test results for pass/fail status
4. Check individual request responses for detailed output

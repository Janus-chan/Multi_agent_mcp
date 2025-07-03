# OCR Agent Testing Guide

This guide provides comprehensive instructions for testing the modified OCR agent that processes image arrays.

## 🚀 Quick Start

### Option 1: Automated Testing with A2A Client (Recommended)

1. **Install dependencies**:
   ```bash
   pip install aiohttp requests
   ```

2. **Start the OCR server**:
   ```bash
   cd Multi_agent_mcp
   python start_ocr_server.py
   ```

3. **Run the test client** (in a new terminal):
   ```bash
   cd Multi_agent_mcp
   python test_a2a_client.py
   ```

### Option 2: Manual Testing with Postman

1. **Start the OCR server**:
   ```bash
   cd Multi_agent_mcp
   python start_ocr_server.py
   ```

2. **Import Postman collection**:
   - Open Postman
   - Import `OCR_Agent_Tests.postman_collection.json`
   - Run the collection

## 📁 Testing Files Overview

| File | Purpose |
|------|---------|
| `test_a2a_client.py` | Automated A2A client for comprehensive testing |
| `start_ocr_server.py` | Simple server starter with health monitoring |
| `POSTMAN_TESTING_GUIDE.md` | Detailed Postman testing instructions |
| `OCR_Agent_Tests.postman_collection.json` | Ready-to-import Postman collection |
| `test_ocr_agent.py` | Unit tests for core functionality |

## 🧪 Test Scenarios

### 1. Image Array Processing
**Purpose**: Test the main functionality with multiple images

**Input**:
```json
[
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
  "/path/to/document.pdf",
  {
    "file": "/path/to/receipt.jpg",
    "name": "Receipt",
    "description": "Purchase receipt"
  }
]
```

**Expected Results**:
- ✅ 4 images processed
- ✅ Each image gets unique UUID
- ✅ Updated names and descriptions
- ✅ OCR text extraction
- ✅ Visual analysis provided

### 2. Single Text Input
**Purpose**: Test backward compatibility

**Input**: `"Please process this image for OCR analysis"`

**Expected Results**:
- ✅ Text processed as single item
- ✅ Structured response format maintained
- ✅ Graceful handling of non-JSON input

### 3. Single Image Object
**Purpose**: Test single image processing

**Input**:
```json
{
  "path": "/path/to/single_document.jpg",
  "name": "Single Document",
  "description": "A single document for OCR processing"
}
```

**Expected Results**:
- ✅ Single image processed correctly
- ✅ Proper metadata enhancement
- ✅ Consistent response structure

### 4. Error Handling
**Purpose**: Test robustness with invalid input

**Input**: `"invalid json [{ broken"`

**Expected Results**:
- ✅ Graceful error handling
- ✅ No server crashes
- ✅ Meaningful error responses

## 🔍 Validation Checklist

When testing, verify these key aspects:

### ✅ **Functional Requirements**
- [ ] Accepts image arrays as input
- [ ] Assigns unique IDs to each image
- [ ] Processes images using MCP OCR tool
- [ ] Returns structured results with updated metadata
- [ ] Handles both JSON array and plain text inputs

### ✅ **Response Structure**
- [ ] Contains `status: "success"`
- [ ] Has `processed_images` count
- [ ] Includes `results` array
- [ ] Each result has all required fields:
  - `id` (unique UUID)
  - `original_name` and `updated_name`
  - `original_description` and `updated_description`
  - `ocr_text`
  - `analysis`

### ✅ **Performance & Reliability**
- [ ] Server starts without errors
- [ ] Responds within reasonable time
- [ ] Handles multiple concurrent requests
- [ ] Maintains consistent response format
- [ ] Logs meaningful information

## 🐛 Troubleshooting

### Common Issues

1. **Server Won't Start**
   ```
   Error: No module named 'a2a'
   ```
   **Solution**: Install required dependencies or run from correct environment

2. **Connection Refused**
   ```
   ConnectionError: [Errno 61] Connection refused
   ```
   **Solution**: Ensure server is running on correct port (8003)

3. **MCP OCR Tool Not Found**
   ```
   Error: No module named 'mcp_ocr'
   ```
   **Solution**: Install or configure the MCP OCR tool

4. **Empty Responses**
   **Solution**: Check server logs for processing errors

### Debug Steps

1. **Check server logs**: Look for error messages in server output
2. **Verify endpoints**: Test agent card endpoint first
3. **Validate JSON**: Ensure request body is properly formatted
4. **Test incrementally**: Start with simple text input, then try arrays

## 📊 Expected Performance

### Response Times
- **Single image**: < 2 seconds
- **Image array (4 items)**: < 5 seconds
- **Large arrays (10+ items)**: < 15 seconds

### Memory Usage
- **Base server**: ~50-100 MB
- **Per image processing**: ~10-20 MB additional

## 🔧 Advanced Testing

### Custom Image Testing
Replace sample paths with real image files:
```json
[
  {
    "path": "/Users/yourname/Documents/invoice.jpg",
    "name": "Real Invoice",
    "description": "Actual invoice document"
  }
]
```

### Load Testing
Use the A2A client to send multiple concurrent requests:
```python
# Modify test_a2a_client.py to run multiple parallel tests
import asyncio

async def load_test():
    tasks = []
    for i in range(10):
        tasks.append(test_image_array_processing())
    await asyncio.gather(*tasks)
```

### Integration Testing
Test with real MCP OCR tools and actual image files to verify end-to-end functionality.

## 📝 Test Reports

After running tests, document:
- ✅ Which scenarios passed/failed
- ⏱️ Response times for different input sizes
- 🐛 Any errors or unexpected behavior
- 💡 Suggestions for improvements

## 🎯 Success Criteria

The OCR agent modifications are working correctly if:
1. ✅ All automated tests pass
2. ✅ Postman collection runs without errors
3. ✅ Image arrays are processed with unique IDs
4. ✅ Structured responses are returned consistently
5. ✅ Both JSON and text inputs are handled properly
6. ✅ Server remains stable under normal load

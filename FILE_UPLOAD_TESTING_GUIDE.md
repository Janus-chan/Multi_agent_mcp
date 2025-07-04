# File Upload Testing Guide for OCR Agent

This guide shows how to test the OCR agent using actual file uploads through the A2A File Upload Client.

## 🚀 Quick Start

### Step 1: Start the OCR Agent Server
```bash
cd Multi_agent_mcp
python start_ocr_server.py
```
Wait for the message: "✅ Server is healthy and responding at http://localhost:8003"

### Step 2: Start the File Upload Client
```bash
# In a new terminal
cd Multi_agent_mcp
pip install aiofiles  # if not already installed
python file_upload_client.py
```
You should see: "✅ Server started successfully!"

### Step 3: Test with Postman
Follow the detailed instructions below.

## 📋 Postman Configuration for File Uploads

### Basic File Upload Test

#### Request Setup:
- **Method**: `POST`
- **URL**: `http://localhost:8004/upload`

#### Headers:
No special headers needed - Postman will automatically set `Content-Type: multipart/form-data`

#### Body Configuration:
1. Go to **Body** tab
2. Select **form-data**
3. Add the following fields:

| Key | Type | Value | Description |
|-----|------|-------|-------------|
| `files` | File | [Select your image file] | **Required** - Image file to process |
| `files` | File | [Select another image file] | **Optional** - Add more files for batch processing |
| `user_id` | Text | `test_user_123` | **Optional** - Custom user ID |
| `description` | Text | `Test OCR processing` | **Optional** - Description for the task |

#### Important Notes:
- Use **`files`** as the key name for all uploaded files
- You can upload multiple files by adding multiple `files` entries
- Supported file types: JPG, PNG, PDF, etc.
- Maximum file size depends on your system configuration

### Sample Request Body (form-data):
```
files: [image1.jpg] (File)
files: [document.pdf] (File)
files: [screenshot.png] (File)
user_id: test_user_123 (Text)
description: Batch OCR processing test (Text)
```

## 📤 Expected Response Format

### Successful Response:
```json
{
  "task_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "context_id": "f1e2d3c4-b5a6-9870-dcba-fe0987654321",
  "user_id": "test_user_123",
  "timestamp": 1704067200000,
  "uploaded_files": 3,
  "files_info": [
    {
      "name": "image1.jpg",
      "original_filename": "image1.jpg"
    },
    {
      "name": "document.pdf", 
      "original_filename": "document.pdf"
    },
    {
      "name": "screenshot.png",
      "original_filename": "screenshot.png"
    }
  ],
  "ocr_result": {
    "task_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "context_id": "f1e2d3c4-b5a6-9870-dcba-fe0987654321",
    "response": {
      "status": "success",
      "processed_images": 3,
      "results": [
        {
          "id": "unique-uuid-1",
          "original_name": "image1.jpg",
          "updated_name": "Updated name based on OCR content",
          "original_description": "Uploaded file: image1.jpg",
          "updated_description": "Detailed description based on OCR analysis",
          "ocr_text": "Extracted text from the image",
          "analysis": "Visual content analysis results"
        }
        // ... more results for each uploaded file
      ]
    }
  },
  "status": "completed"
}
```

## 🧪 Test Scenarios

### Test 1: Single Image Upload
**Purpose**: Test basic file upload functionality

**Setup**:
- Upload one image file (JPG/PNG)
- No additional form fields

**Expected**: 
- ✅ File processed successfully
- ✅ OCR text extracted
- ✅ Unique ID assigned
- ✅ Metadata generated

### Test 2: Multiple Image Upload
**Purpose**: Test batch processing

**Setup**:
- Upload 3-5 different image files
- Add custom `user_id` and `description`

**Expected**:
- ✅ All files processed
- ✅ Each file gets unique ID
- ✅ Batch processing completed
- ✅ Custom metadata included

### Test 3: Mixed File Types
**Purpose**: Test different file format handling

**Setup**:
- Upload JPG, PNG, and PDF files
- Mix of document types (invoices, screenshots, etc.)

**Expected**:
- ✅ All formats processed
- ✅ Appropriate OCR for each type
- ✅ Different analysis for different content

### Test 4: Large File Upload
**Purpose**: Test file size limits

**Setup**:
- Upload larger image files (>5MB)
- Monitor processing time

**Expected**:
- ✅ Large files handled gracefully
- ✅ Reasonable processing time
- ✅ No timeout errors

## 🔍 Validation Checklist

After each test, verify:

### ✅ **Request Processing**
- [ ] HTTP 200 status code
- [ ] Response contains `task_id` and `context_id`
- [ ] `uploaded_files` count matches files sent
- [ ] `files_info` array contains all uploaded files

### ✅ **A2A Protocol Fields**
- [ ] `task_id` is a valid UUID
- [ ] `context_id` is a valid UUID  
- [ ] `user_id` is set (custom or auto-generated)
- [ ] `timestamp` is a valid Unix timestamp

### ✅ **OCR Processing**
- [ ] `ocr_result` contains the agent response
- [ ] Each file has unique `id` in results
- [ ] `ocr_text` field contains extracted content
- [ ] `analysis` field provides visual analysis
- [ ] `updated_name` and `updated_description` are enhanced

## 🐛 Troubleshooting

### Common Issues:

1. **Connection Refused (Port 8004)**
   ```
   Error: connect ECONNREFUSED 127.0.0.1:8004
   ```
   **Solution**: Ensure file upload client is running

2. **OCR Agent Not Found**
   ```json
   {"error": "Failed to communicate with OCR agent"}
   ```
   **Solution**: Ensure OCR agent is running on port 8003

3. **File Upload Failed**
   ```json
   {"error": "No files uploaded"}
   ```
   **Solution**: Ensure you're using `files` as the key name in form-data

4. **Large File Timeout**
   ```json
   {"error": "OCR processing timeout"}
   ```
   **Solution**: Try smaller files or increase timeout settings

### Debug Steps:

1. **Check both servers are running**:
   - OCR Agent: http://localhost:8003/.well-known/agent.json
   - Upload Client: http://localhost:8004/health

2. **Verify file upload client logs**:
   - Look for "Received file:" messages
   - Check for forwarding success/failure

3. **Test with small files first**:
   - Start with simple JPG images
   - Gradually increase complexity

## 📊 Performance Expectations

### File Upload Times:
- **Small images (<1MB)**: < 5 seconds
- **Medium images (1-5MB)**: < 15 seconds  
- **Large images (>5MB)**: < 30 seconds
- **Batch (5 files)**: < 45 seconds

### Response Size:
- Expect detailed JSON responses
- OCR text length varies by image content
- Analysis provides comprehensive descriptions

## 🎯 Success Indicators

The file upload system is working correctly when:

1. ✅ **Files upload successfully** without errors
2. ✅ **A2A fields are auto-generated** (UUIDs, timestamps)
3. ✅ **OCR processing completes** for all uploaded files
4. ✅ **Unique IDs assigned** to each processed image
5. ✅ **Structured responses** with enhanced metadata
6. ✅ **Both servers remain stable** during processing

## 🔧 Advanced Usage

### Custom User IDs:
Use meaningful user IDs for tracking:
```
user_id: department_finance_001
```

### Descriptive Tasks:
Add context for better processing:
```
description: Invoice processing for Q4 2024 audit
```

### Batch Organization:
Group related files in single uploads for better organization and processing efficiency.

# Independent Services Guide

This guide shows how to run the OCR Agent and File Upload Client as separate, independent processes.

## 🚀 **Starting Services Independently**

### **Prerequisites**
```bash
cd Multi_agent_mcp
pip install aiohttp aiofiles requests
```

### **1. Start OCR Agent Server (Port 8003)**

**Terminal 1:**
```bash
cd Multi_agent_mcp/ocr_agent
python _main_.py --host localhost --port 8003
```

**Expected Output:**
```
INFO:root:Initializing OCR Agent with MCP OCR tool integration
INFO:root:Starting OCR Agent server on http://localhost:8003
INFO:root:Agent Name: OCR Image Processing Agent, Version: 1.0.0
INFO:root:A2A RPC Endpoint: http://localhost:8003/a2a/ocr_agent
INFO:root:Agent Card: http://localhost:8003/.well-known/agent.json
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://localhost:8003 (Press CTRL+C to quit)
```

**Verify OCR Agent is Running:**
```bash
curl http://localhost:8003/.well-known/agent.json
```

### **2. Start File Upload Client (Port 8004)**

**Terminal 2:**
```bash
cd Multi_agent_mcp
python file_upload_client.py --port 8004 --ocr-agent-url http://localhost:8003
```

**Expected Output:**
```
A2A File Upload Client for OCR Processing
=============================================
Client Port: 8004
OCR Agent URL: http://localhost:8003

🚀 A2A File Upload Client started on http://localhost:8004
📁 Upload endpoint: http://localhost:8004/upload
🔗 OCR Agent URL: http://localhost:8003
ℹ️  Info page: http://localhost:8004/
✅ Server started successfully!
📤 Upload files at: http://localhost:8004/upload
🌐 Info page: http://localhost:8004/
📋 Use Ctrl+C to stop the server
```

**Verify File Upload Client is Running:**
```bash
curl http://localhost:8004/health
```

### **3. Test Both Services**

**Terminal 3:**
```bash
cd Multi_agent_mcp
python test_endpoints.py
```

## 📤 **Sending Images via Form-Data**

### **Method 1: Postman (Recommended)**

#### **Request Configuration:**
- **Method**: `POST`
- **URL**: `http://localhost:8004/upload`
- **Body**: `form-data`

#### **Form-Data Fields:**
| Key | Type | Value | Required |
|-----|------|-------|----------|
| `files` | File | [Select your image] | ✅ Yes |
| `files` | File | [Select another image] | ❌ Optional |
| `user_id` | Text | `my_user_123` | ❌ Optional |
| `description` | Text | `OCR processing task` | ❌ Optional |

#### **Step-by-Step Postman Setup:**
1. Open Postman
2. Create new request
3. Set method to `POST`
4. Set URL to `http://localhost:8004/upload`
5. Go to **Body** tab
6. Select **form-data**
7. Add fields as shown in table above
8. For `files` fields, click dropdown and select **File**
9. Click **Select Files** and choose your images
10. Click **Send**

### **Method 2: cURL Command**
```bash
curl -X POST http://localhost:8004/upload \
  -F "files=@/path/to/your/image1.jpg" \
  -F "files=@/path/to/your/image2.png" \
  -F "user_id=test_user_123" \
  -F "description=Test OCR processing"
```

### **Method 3: Python Script**
```python
import requests

# Prepare files
files = [
    ('files', ('image1.jpg', open('path/to/image1.jpg', 'rb'), 'image/jpeg')),
    ('files', ('image2.png', open('path/to/image2.png', 'rb'), 'image/png'))
]

# Optional metadata
data = {
    'user_id': 'python_user_123',
    'description': 'Python API test'
}

# Send request
response = requests.post('http://localhost:8004/upload', files=files, data=data)
print(response.json())

# Close files
for _, file_tuple in files:
    file_tuple[1].close()
```

## 📋 **Expected Response Format**

### **Successful Upload Response:**
```json
{
  "task_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "context_id": "f1e2d3c4-b5a6-9870-dcba-fe0987654321",
  "user_id": "my_user_123",
  "timestamp": 1704067200000,
  "uploaded_files": 2,
  "files_info": [
    {
      "name": "image1.jpg",
      "original_filename": "image1.jpg"
    },
    {
      "name": "image2.png", 
      "original_filename": "image2.png"
    }
  ],
  "ocr_result": {
    "task_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "context_id": "f1e2d3c4-b5a6-9870-dcba-fe0987654321",
    "response": {
      "status": "success",
      "processed_images": 2,
      "results": [
        {
          "id": "unique-uuid-1",
          "original_name": "image1.jpg",
          "updated_name": "Invoice Document",
          "original_description": "Uploaded file: image1.jpg",
          "updated_description": "Invoice from ABC Company dated 2024",
          "ocr_text": "INVOICE\nABC Company\nDate: 2024-01-15\nAmount: $1,234.56",
          "analysis": "This is an invoice document with company header and amount"
        },
        {
          "id": "unique-uuid-2",
          "original_name": "image2.png",
          "updated_name": "Screenshot Image",
          "original_description": "Uploaded file: image2.png",
          "updated_description": "Application interface screenshot",
          "ocr_text": "Username:\nPassword:\nLogin",
          "analysis": "Application login interface with input fields"
        }
      ]
    }
  },
  "status": "completed"
}
```

## 🔍 **Key Features**

### **✅ Automatic A2A Protocol Handling**
- **task_id**: Auto-generated UUID
- **context_id**: Auto-generated UUID
- **user_id**: Auto-generated or custom
- **timestamp**: Current Unix timestamp

### **✅ File Processing**
- **Multiple files**: Upload several images at once
- **File validation**: Checks for valid uploads
- **Temporary storage**: Files processed and cleaned up automatically
- **Metadata extraction**: File names, sizes, and types

### **✅ OCR Integration**
- **Forwards to OCR agent**: Uses proper A2A protocol
- **Structured results**: Each image gets unique ID
- **Enhanced metadata**: Updated names and descriptions
- **Comprehensive analysis**: OCR text + visual analysis

## 🐛 **Troubleshooting**

### **Common Issues:**

1. **OCR Agent 404 Error:**
   ```json
   {"error": "OCR agent returned status 404"}
   ```
   **Solution**: Ensure OCR agent is running and accessible at `/a2a/ocr_agent`

2. **File Upload Client Connection Error:**
   ```
   Connection refused on port 8004
   ```
   **Solution**: Make sure file upload client is running

3. **No Files Uploaded:**
   ```json
   {"error": "No files uploaded"}
   ```
   **Solution**: Use `files` as the key name in form-data

4. **File Size 0 Bytes:**
   **Solution**: Ensure files are properly selected in Postman

### **Debug Commands:**
```bash
# Check services are running
curl http://localhost:8003/.well-known/agent.json
curl http://localhost:8004/health

# Test endpoint connectivity
python test_endpoints.py

# Check ports
netstat -an | grep :8003
netstat -an | grep :8004
```

## 🎯 **Service Architecture**

```
┌─────────────────┐    Form-Data     ┌──────────────────┐    A2A Protocol    ┌─────────────────┐
│   Postman/      │   File Upload    │  File Upload     │   JSON Request     │   OCR Agent     │
│   Client        │ ────────────────▶│  Client          │ ──────────────────▶│   Server        │
│   (Port N/A)    │                  │  (Port 8004)     │                    │   (Port 8003)   │
└─────────────────┘                  └──────────────────┘                    └─────────────────┘
                                             │                                          │
                                             │ Auto-generates:                         │ Processes:
                                             │ • task_id (UUID)                        │ • OCR analysis
                                             │ • context_id (UUID)                     │ • Text extraction
                                             │ • user_id                               │ • Image analysis
                                             │ • timestamp                             │ • Metadata enhancement
                                             │ • File processing                       │
                                             ▼                                          ▼
                                      ┌──────────────────┐                    ┌─────────────────┐
                                      │  Structured      │◀───────────────────│  OCR Results    │
                                      │  Response        │                    │  with Unique    │
                                      │  with Metadata   │                    │  IDs            │
                                      └──────────────────┘                    └─────────────────┘
```

## 🎉 **Success Indicators**

Your system is working correctly when:
- ✅ Both services start without errors
- ✅ Endpoint tests pass
- ✅ Files upload successfully via form-data
- ✅ OCR processing completes with unique IDs
- ✅ Structured JSON responses are returned
- ✅ File cleanup happens automatically

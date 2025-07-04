# Quick Fix Guide for A2A Upload Issues

## 🔧 **Issues Fixed**

### **1. A2A JSON-RPC Format Error**
**Problem**: The file upload client was sending data in wrong format, causing validation errors.

**Solution**: Updated `forward_to_ocr_agent` method to use proper A2A JSON-RPC format:
```json
{
  "jsonrpc": "2.0",
  "method": "message/send",
  "params": {
    "task_id": "uuid",
    "context_id": "uuid",
    "user_id": "user",
    "timestamp": 1234567890,
    "message": {
      "content": "[file_array]",
      "metadata": {...}
    }
  },
  "id": "uuid"
}
```

### **2. File Reading Issue**
**Problem**: Files were showing 0 bytes due to incorrect async reading.

**Solution**: Changed from chunk-based reading to complete file reading:
```python
# Old (problematic)
async for chunk in field:
    await f.write(chunk)

# New (fixed)
file_content = await field.read()
await f.write(file_content)
```

## 🚀 **Testing the Fixes**

### **Step 1: Restart Both Services**

**Terminal 1 - OCR Agent:**
```bash
cd Multi_agent_mcp/ocr_agent
python _main_.py --host localhost --port 8003
```

**Terminal 2 - File Upload Client:**
```bash
cd Multi_agent_mcp
python file_upload_client.py --port 8004 --ocr-agent-url http://localhost:8003
```

### **Step 2: Test Correct A2A Format**
```bash
cd Multi_agent_mcp
python test_correct_a2a.py
```

**Expected Output:**
```
✅ Direct A2A request successful!
✅ File upload validation working
🎉 A2A JSON-RPC format is working!
```

### **Step 3: Test File Upload in Postman**

**Request Configuration:**
- **Method**: `POST`
- **URL**: `http://localhost:8004/upload`
- **Body**: `form-data`
- **Fields**:
  - `files`: [Select an image file] (File)
  - `user_id`: `test_user` (Text, optional)
  - `description`: `Test upload` (Text, optional)

**Expected Response:**
```json
{
  "task_id": "uuid",
  "context_id": "uuid", 
  "user_id": "test_user",
  "timestamp": 1704067200000,
  "uploaded_files": 1,
  "files_info": [
    {
      "name": "image.jpg",
      "original_filename": "image.jpg"
    }
  ],
  "ocr_result": {
    "jsonrpc": "2.0",
    "result": {
      "task_id": "uuid",
      "context_id": "uuid",
      "response": {
        "status": "success",
        "processed_images": 1,
        "results": [
          {
            "id": "unique-uuid",
            "original_name": "image.jpg",
            "updated_name": "Enhanced name",
            "ocr_text": "Extracted text",
            "analysis": "Image analysis"
          }
        ]
      }
    },
    "id": "uuid"
  },
  "status": "completed"
}
```

## 🔍 **Verification Checklist**

### ✅ **File Upload Client Logs Should Show:**
```
INFO - Received file: image.jpg (12345 bytes)  # Non-zero bytes!
INFO - Processing 1 uploaded files
INFO - Forwarding to OCR agent: http://localhost:8003/a2a/ocr_agent
INFO - OCR agent responded successfully
```

### ✅ **OCR Agent Logs Should Show:**
```
INFO - Starting OCR Agent server on http://localhost:8003
INFO - A2A RPC Endpoint: http://localhost:8003/a2a/ocr_agent
# No validation errors!
```

### ✅ **Postman Response Should Have:**
- ✅ Non-zero file size in logs
- ✅ `ocr_result` with `jsonrpc: "2.0"`
- ✅ `result` field instead of `error`
- ✅ Proper OCR processing results

## 🐛 **Troubleshooting**

### **If you still see validation errors:**
1. **Check A2A format**: Run `python test_a2a_format.py`
2. **Verify endpoints**: Ensure `/a2a/ocr_agent` is accessible
3. **Check logs**: Look for specific validation error messages

### **If files still show 0 bytes:**
1. **Check file selection**: Ensure files are properly selected in Postman
2. **Try different files**: Test with small image files first
3. **Check permissions**: Ensure temp directory is writable

### **If OCR processing fails:**
1. **Check MCP OCR tool**: Ensure `mcp_ocr` module is available
2. **Test simple text**: Try with plain text input first
3. **Check dependencies**: Verify all required packages are installed

## 🎯 **Success Indicators**

Your system is working correctly when:
1. ✅ **File size > 0 bytes** in upload client logs
2. ✅ **No validation errors** in OCR agent logs  
3. ✅ **JSON-RPC response** with `result` field
4. ✅ **OCR processing completes** with unique IDs
5. ✅ **Structured results** returned to Postman

## 📋 **Next Steps**

Once the fixes are working:
1. **Test with real images**: Upload actual JPG/PNG files
2. **Test batch uploads**: Upload multiple files at once
3. **Verify OCR results**: Check that text extraction works
4. **Test error handling**: Try invalid files or large files

The system should now properly handle file uploads and process them through the OCR agent with correct A2A protocol formatting!

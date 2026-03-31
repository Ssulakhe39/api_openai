# Quick Start Guide - Aerial Image Segmentation

## Prerequisites

- Python 3.8+ with pip
- Node.js 16+ with npm
- Sample aerial images (JPG, PNG, or TIFF)

## Setup

### 1. Install Backend Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Install Frontend Dependencies

```bash
cd frontend
npm install
```

## Running the Application

### Start Backend Server

```bash
# From project root
cd backend
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

Backend will be available at: http://localhost:8000

### Start Frontend Server

```bash
# From project root (in a new terminal)
cd frontend
npm run dev
```

Frontend will be available at: http://localhost:5173 (or port shown in terminal)

## Using the Application

1. **Open Browser:** Navigate to http://localhost:5173

2. **Upload Image:**
   - Click "Choose File" and select an aerial image (JPG, PNG, or TIFF)
   - Click "Upload" button
   - Wait for upload to complete
   - Image will appear in the "Original Image" panel

3. **Select Model:**
   - Choose from dropdown: SAM2, YOLOv8, or U-Net
   - Default is first available model

4. **Run Segmentation:**
   - Click "Run Segmentation" button
   - Wait for processing (may take 10-60 seconds depending on image size and model)
   - Results will appear in three panels:
     - Left: Original image
     - Middle: Black/white segmentation mask
     - Right: Red overlay on original image

5. **Try Different Models:**
   - Select a different model from dropdown
   - Click "Run Segmentation" again
   - Compare results across models

## Troubleshooting

### Backend Won't Start

**Error:** `ModuleNotFoundError: No module named 'backend'`

**Solution:** Make sure you're running from the `backend` directory:
```bash
cd backend
python -m uvicorn api.main:app --reload
```

### Frontend Won't Start

**Error:** `'vite' is not recognized`

**Solution:** Install dependencies:
```bash
cd frontend
npm install
```

### CORS Errors

**Error:** `Access to fetch at 'http://localhost:8000/...' has been blocked by CORS policy`

**Solution:** Backend CORS is configured for common ports. If using a different port, update `backend/api/main.py`:
```python
allow_origins=[
    "http://localhost:YOUR_PORT",
]
```

### Images Not Loading

**Error:** Images don't appear after upload/segmentation

**Solution:** 
1. Check backend console for errors
2. Verify `backend/uploads/images/` and `backend/uploads/masks/` directories exist
3. Check browser console for 404 errors

### Segmentation Takes Too Long

**Note:** First run may be slow as models load. Subsequent runs should be faster.

**Tips:**
- Use smaller images (< 2048x2048) for faster processing
- YOLOv8 is typically fastest
- SAM2 may take longer but provides better quality

## Sample Workflow

```bash
# Terminal 1 - Backend
cd backend
python -m uvicorn api.main:app --reload

# Terminal 2 - Frontend  
cd frontend
npm run dev

# Browser
# 1. Open http://localhost:5173
# 2. Upload aerial image
# 3. Select model (e.g., YOLOv8)
# 4. Click "Run Segmentation"
# 5. View results in three panels
```

## API Endpoints

Test backend directly:

```bash
# Check API is running
curl http://localhost:8000/

# Get available models
curl http://localhost:8000/models

# Upload image (replace with your file)
curl -X POST http://localhost:8000/upload \
  -F "file=@path/to/image.jpg"

# Run segmentation (replace IMAGE_ID)
curl -X POST http://localhost:8000/segment \
  -H "Content-Type: application/json" \
  -d '{"image_id": "IMAGE_ID", "model": "yolov8"}'
```

## Next Steps

- See [frontend/TESTING.md](frontend/TESTING.md) for detailed testing instructions
- See [frontend/README.md](frontend/README.md) for architecture details
- See [SETUP.md](SETUP.md) for complete setup instructions
- See [frontend/IMPLEMENTATION_SUMMARY.md](frontend/IMPLEMENTATION_SUMMARY.md) for implementation details

## Support

For issues or questions:
1. Check browser console for errors
2. Check backend terminal for error logs
3. Verify all dependencies are installed
4. Ensure both servers are running

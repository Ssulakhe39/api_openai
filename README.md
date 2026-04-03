# Aerial Image Segmentation Application

A full-stack web application for automated building detection and boundary extraction from aerial imagery using state-of-the-art deep learning models. Upload drone or satellite images, run AI-powered segmentation, detect building boundaries, and export results in multiple formats.

## 🌟 Features

### Single Image Processing
- Upload aerial images (JPG, PNG, TIFF) up to 50MB
- Choose from three segmentation models (SAM2, YOLOv8, Mask R-CNN)
- Real-time segmentation with visual feedback
- Three-panel visualization (original, mask, overlay)
- OpenCV-based boundary detection with polygon extraction
- GPT-enhanced boundary detection with interactive editing
- Edit, add, and delete building polygons on canvas
- Export results as JSON with polygon coordinates

### Batch Processing
- Upload ZIP archives containing multiple aerial images
- Process up to 50 images per batch
- Sequential segmentation across all images
- Per-image polygon review and editing
- Bulk download in JSON, PNG, or JPEG formats
- Progress tracking with per-image status indicators
- Individual item retry on failure

### User Management
- Secure authentication system
- User registration and login
- Session-based access control
- Protected API endpoints

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (Vite + Vanilla JS)              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Image Upload │  │ Model Select │  │ Segmentation │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Batch Upload │  │ Polygon Edit │  │ Visualization│      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ REST API (HTTP/JSON)
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                   Backend (FastAPI + Python)                 │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              API Endpoints                            │   │
│  │  • /upload         • /segment      • /boundaries     │   │
│  │  • /batch/*        • /auth/*       • /models         │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │           Segmentation Models                         │   │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐     │   │
│  │  │ SAM2       │  │ YOLOv8     │  │ Mask R-CNN │     │   │
│  │  └────────────┘  └────────────┘  └────────────┘     │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │           Boundary Detection                          │   │
│  │  • OpenCV contour detection                          │   │
│  │  • GPT-enhanced boundary extraction                  │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## 📁 Project Structure

```
aerial-image-segmentation/
├── backend/
│   ├── api/
│   │   ├── __init__.py
│   │   └── main.py                    # FastAPI application & endpoints
│   ├── models/
│   │   ├── segmentation_model.py      # Abstract base class
│   │   ├── segmentation_model_manager.py
│   │   ├── sam2_adapter.py            # SAM2 implementation
│   │   ├── yolov8_adapter.py          # YOLOv8 implementation
│   │   ├── maskrcnn_adapter.py        # Mask R-CNN implementation
│   │   └── unet_adapter.py            # U-Net implementation
│   ├── utils/
│   │   ├── image_processor.py         # Image validation & processing
│   │   ├── boundary_detector.py       # OpenCV boundary detection
│   │   └── gpt_boundary.py            # GPT boundary detection
│   ├── tests/                         # Comprehensive test suite
│   ├── uploads/                       # Uploaded images storage
│   ├── requirements.txt
│   ├── run_server.py                  # Server startup script
│   └── .env.example                   # Environment configuration template
├── frontend/
│   ├── src/
│   │   ├── index.js                   # Main application
│   │   ├── appState.js                # State management
│   │   ├── imageUploader.js           # Upload component
│   │   ├── modelSelector.js           # Model selection
│   │   ├── segmentationRunner.js      # Segmentation execution
│   │   ├── visualizationPanel.js      # Results display
│   │   ├── boundaryDetector.js        # OpenCV boundary UI
│   │   ├── gptBoundaryDetector.js     # GPT boundary UI
│   │   ├── batchProcessor.js          # Batch processing UI
│   │   ├── batchPolygonEditor.js      # Batch polygon editor
│   │   ├── dashboard.js               # User dashboard
│   │   └── styles.css                 # Application styles
│   ├── index.html                     # Main page
│   ├── login.html                     # Login/register page
│   ├── package.json
│   └── vite.config.js
├── .kiro/
│   └── specs/
│       └── batch-zip-segmentation/    # Feature specifications
├── README.md                          # This file
└── APPLICATION_SUMMARY.md             # Detailed implementation summary
```

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- Node.js 16 or higher
- pip (Python package manager)
- npm (Node package manager)
- 8GB+ RAM (16GB+ recommended)
- GPU with CUDA support (optional, for faster inference)

### Backend Setup

1. **Navigate to backend directory**
   ```bash
   cd backend
   ```

2. **Create and activate virtual environment**
   ```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Download model weights** (see Model Setup section below)

6. **Start the backend server**
   ```bash
   python run_server.py
   ```
   
   The API will be available at `http://localhost:8000`

### Frontend Setup

1. **Navigate to frontend directory**
   ```bash
   cd frontend
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Start development server**
   ```bash
   npm run dev
   ```
   
   The application will be available at `http://localhost:3000`

4. **Open in browser**
   - Navigate to `http://localhost:3000`
   - Create an account or login
   - Start uploading and processing images!

## 🤖 Model Setup

The application supports three segmentation models. You need to download the model weights before using them.

### SAM2 (Segment Anything Model 2)

```bash
cd backend/models
# Download from Meta AI
wget https://dl.fbaipublicfiles.com/segment_anything_2/sam2_hiera_large.pt
```

Or manually download from: https://github.com/facebookresearch/segment-anything-2

### YOLOv8

The YOLOv8 model will be automatically downloaded on first use by Ultralytics. For custom aerial-trained models:

```bash
cd backend/models
# Use the provided download script
python ../download_yolo_aerial.py
```

### Mask R-CNN

```bash
cd backend/models
# Download pre-trained weights
# Model will be loaded from torchvision if not present
```

### Model Configuration

Edit `backend/.env` to specify model paths:

```env
SAM2_CHECKPOINT_PATH=models/sam2_hiera_large.pt
SAM2_MODEL_CFG=sam2_hiera_l.yaml
YOLOV8_MODEL_PATH=models/yolov8n-seg.pt
```

## 📖 Usage Guide

### Single Image Workflow

1. **Upload Image**
   - Click "Choose File" and select an aerial image
   - Supported formats: JPG, PNG, TIFF (max 50MB)
   - Click "Upload" button

2. **Select Model**
   - Choose from dropdown: SAM2, YOLOv8, or Mask R-CNN
   - Each model has different speed/accuracy tradeoffs

3. **Run Segmentation**
   - Click "Run Segmentation"
   - Wait for processing (10-60 seconds depending on image size)
   - View results in three panels: Original, Mask, Overlay

4. **Detect Boundaries**
   - Click "Detect GPT Boundaries" for enhanced detection
   - Review detected building polygons
   - Click "Edit Polygons" to modify boundaries

5. **Edit Polygons**
   - Drag polygon corners to adjust shape
   - Click "Draw Polygon" to add new buildings
   - Click "Delete Polygon" then click a polygon to remove it
   - Click "Done Editing" to save changes

6. **Export Results**
   - Results are automatically saved
   - JSON files contain polygon coordinates and building counts

### Batch Processing Workflow

1. **Prepare ZIP Archive**
   - Create a ZIP file containing aerial images
   - Max 50 images per ZIP
   - Max 500MB total size

2. **Upload ZIP**
   - In the "Batch Processing" section, select your ZIP file
   - Click "Upload ZIP"
   - View list of extracted images

3. **Select Model**
   - Choose segmentation model for entire batch
   - All images will use the same model

4. **Run Batch**
   - Click "Run Batch Processing"
   - Monitor progress for each image
   - Processing happens sequentially

5. **Review Results**
   - View thumbnail grid of all processed images
   - Click any thumbnail to edit its polygons
   - Make adjustments as needed

6. **Download Results**
   - Select output format: JSON, PNG, or JPEG
   - Click "Download All"
   - Receive ZIP file with all results

## 🔌 API Documentation

### Authentication Endpoints

#### POST /api/auth/register
Register a new user account.

**Request:**
```json
{
  "username": "user123",
  "password": "securepass"
}
```

**Response:**
```json
{
  "token": "auth_token_here",
  "username": "user123"
}
```

#### POST /api/auth/login
Login to existing account.

**Request:**
```json
{
  "username": "user123",
  "password": "securepass"
}
```

**Response:**
```json
{
  "token": "auth_token_here",
  "username": "user123"
}
```

### Image Processing Endpoints

#### POST /upload
Upload a single aerial image.

**Request:** `multipart/form-data` with `file` field

**Response:**
```json
{
  "image_id": "uuid-here",
  "image_url": "/images/uuid-here.jpg",
  "width": 1024,
  "height": 768
}
```

#### POST /segment
Run segmentation on uploaded image.

**Request:**
```json
{
  "image_id": "uuid-here",
  "model": "yolov8"
}
```

**Response:**
```json
{
  "mask_url": "/masks/uuid-here-mask.png",
  "mask_base64": "base64_encoded_mask",
  "processing_time": 12.34,
  "model_used": "yolov8"
}
```

#### POST /boundaries
Detect building boundaries from segmentation mask.

**Request:**
```json
{
  "image_id": "uuid-here",
  "model": "yolov8"
}
```

**Response:**
```json
{
  "overlay_url": "/overlays/uuid-here-overlay.png",
  "building_count": 15,
  "polygons": [
    {
      "id": 1,
      "coordinates": [[x1, y1], [x2, y2], ...]
    }
  ]
}
```

#### POST /gpt-boundaries
GPT-enhanced boundary detection.

**Request:**
```json
{
  "image_id": "uuid-here",
  "model": "yolov8"
}
```

**Response:**
```json
{
  "overlay_url": "/overlays/uuid-here-gpt-overlay.png",
  "building_count": 15,
  "polygons": [...],
  "processing_time": 8.5
}
```

#### GET /models
List available segmentation models.

**Response:**
```json
{
  "models": [
    {
      "name": "sam2",
      "display_name": "SAM2 (Segment Anything)",
      "description": "Foundation model for general-purpose segmentation"
    },
    {
      "name": "yolov8",
      "display_name": "YOLOv8 Segmentation",
      "description": "Real-time instance segmentation"
    },
    {
      "name": "maskrcnn",
      "display_name": "Mask R-CNN",
      "description": "Instance segmentation with region proposals"
    }
  ]
}
```

### Batch Processing Endpoints

#### POST /api/batch/upload-zip
Upload ZIP archive for batch processing.

**Request:** `multipart/form-data` with `file` field

**Response:**
```json
{
  "batch_id": "batch-uuid",
  "filenames": ["img1.png", "img2.jpg"],
  "total_images": 2
}
```

#### POST /api/batch/{batch_id}/run
Start batch processing.

**Request:**
```json
{
  "model": "yolov8"
}
```

**Response:**
```json
{
  "status": "started"
}
```

#### GET /api/batch/{batch_id}/status
Get batch processing status.

**Response:**
```json
{
  "batch_id": "batch-uuid",
  "status": "running",
  "model": "yolov8",
  "items": [
    {
      "item_id": "item-uuid",
      "original_filename": "img1.png",
      "status": "done",
      "building_count": 12,
      "polygons": [...]
    }
  ],
  "total": 2,
  "done": 1,
  "failed": 0
}
```

#### GET /api/batch/{batch_id}/download?format=json
Download batch results.

**Query Parameters:**
- `format`: `json` | `png` | `jpeg` (default: `json`)

**Response:** ZIP file download

#### POST /api/batch/{batch_id}/items/{item_id}/retry
Retry failed batch item.

**Response:** Updated item status

## ⚙️ Configuration

### Backend Configuration (.env)

```env
# Server settings
HOST=0.0.0.0
PORT=8000

# File upload settings
MAX_UPLOAD_SIZE_MB=50
UPLOAD_DIR=uploads
MASK_DIR=masks

# Model paths
SAM2_CHECKPOINT_PATH=models/sam2_hiera_large.pt
SAM2_MODEL_CFG=sam2_hiera_l.yaml
YOLOV8_MODEL_PATH=models/yolov8n-seg.pt

# CORS settings
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

### Frontend Configuration

The frontend uses Vite for development. Configuration is in `frontend/vite.config.js`:

```javascript
export default {
  server: {
    port: 3000,
    proxy: {
      '/api': 'http://localhost:8000'
    }
  }
}
```

## 🧪 Testing

### Backend Tests

The backend includes comprehensive test coverage with 158+ tests.

```bash
cd backend
pytest

# Run with coverage
pytest --cov=api --cov=models --cov=utils

# Run specific test file
pytest tests/test_api_setup.py
```

**Test Categories:**
- API endpoint tests
- Model adapter tests
- Image processor tests
- Boundary detection tests
- Integration tests
- Error handling tests

### Frontend Tests

```bash
cd frontend
npm test

# Watch mode
npm run test:watch
```

## 📊 Performance

### Processing Times (Approximate)

| Model | 512x512 | 1024x1024 | 2048x2048 |
|-------|---------|-----------|-----------|
| SAM2 | 10-20s | 30-45s | 60-90s |
| YOLOv8 | 3-5s | 8-12s | 15-25s |
| Mask R-CNN | 5-10s | 15-25s | 30-50s |

*Times vary based on hardware (GPU vs CPU) and image complexity*

### Resource Requirements

**Minimum:**
- CPU: 4 cores
- RAM: 8GB
- Storage: 10GB
- Python 3.8+
- Node.js 16+

**Recommended:**
- CPU: 8+ cores
- RAM: 16GB+
- GPU: NVIDIA GPU with 8GB+ VRAM (CUDA support)
- Storage: 20GB+
- Python 3.9+
- Node.js 18+

## 🔒 Security

### Implemented Security Measures

1. **File Validation**
   - Extension whitelist (JPG, PNG, TIFF only)
   - File integrity checking
   - Size limits (50MB per image, 500MB per ZIP)
   - MIME type validation

2. **Input Sanitization**
   - UUID-based file IDs (no user-controlled paths)
   - Model name validation against whitelist
   - Request body validation using Pydantic

3. **Authentication**
   - Session-based authentication
   - Password hashing (bcrypt)
   - Protected API endpoints
   - Token-based access control

4. **Error Handling**
   - No sensitive information in error messages
   - Proper HTTP status codes
   - Server-side logging only

5. **CORS Configuration**
   - Restricted to specific origins
   - Configurable for production

### Security Best Practices

- Always use HTTPS in production
- Implement rate limiting
- Regular security audits
- Keep dependencies updated
- Use environment variables for secrets
- Implement proper logging and monitoring

## 🐛 Troubleshooting

### Backend Issues

**Server won't start:**
- Check Python version: `python --version` (need 3.8+)
- Verify dependencies: `pip install -r requirements.txt`
- Check port 8000 is available: `netstat -an | findstr 8000`
- Review logs for error messages

**Model loading fails:**
- Verify model weights are downloaded
- Check paths in `.env` file
- Ensure sufficient memory available
- Check CUDA availability for GPU: `python -c "import torch; print(torch.cuda.is_available())"`

**Segmentation fails:**
- Check image format is supported
- Verify image isn't corrupted
- Ensure sufficient memory
- Review backend logs

### Frontend Issues

**Frontend won't start:**
- Check Node.js version: `node --version` (need 16+)
- Install dependencies: `npm install`
- Check port 3000 is available
- Clear npm cache: `npm cache clean --force`

**CORS errors:**
- Verify backend is running
- Check CORS configuration in `backend/api/main.py`
- Ensure frontend URL is in allowed origins
- Check browser console for specific error

**Images not loading:**
- Verify backend static file serving is configured
- Check image URLs in network tab
- Ensure uploads directory exists and has correct permissions

**Login issues:**
- Clear browser session storage
- Check backend authentication endpoints
- Verify credentials are correct
- Check network tab for API errors

### Common Issues

**Out of memory:**
- Reduce image size before upload
- Close other applications
- Use smaller model (YOLOv8 instead of SAM2)
- Add more RAM or use GPU

**Slow processing:**
- Use GPU if available
- Reduce image resolution
- Choose faster model (YOLOv8)
- Process images in smaller batches

**Batch processing stuck:**
- Check backend logs for errors
- Verify all images in ZIP are valid
- Reduce batch size (< 50 images)
- Check available disk space

## 📚 Additional Documentation

- `APPLICATION_SUMMARY.md` - Comprehensive implementation details
- `frontend/README.md` - Frontend-specific documentation
- `frontend/TESTING.md` - Testing guide
- `backend/YOLOV8_AERIAL_GUIDE.md` - YOLOv8 model guide
- `.kiro/specs/` - Feature specifications and design documents

## 🤝 Contributing

Contributions are welcome! Please follow these guidelines:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Make your changes
4. Add tests for new features
5. Ensure all tests pass: `pytest` and `npm test`
6. Commit with clear messages
7. Push to your fork
8. Submit a pull request

### Code Style

**Python:**
- Follow PEP 8
- Use type hints
- Document functions with docstrings
- Maximum line length: 100 characters

**JavaScript:**
- Use ES6+ features
- Consistent naming (camelCase)
- Document complex functions
- Use async/await for promises

## 📄 License

MIT License - See LICENSE file for details

## 🙏 Acknowledgments

- **SAM2:** Meta AI Research
- **YOLOv8:** Ultralytics
- **Mask R-CNN:** Facebook AI Research
- **FastAPI:** Sebastián Ramírez
- **Vite:** Evan You and contributors

## 📞 Support

For issues, questions, or contributions:
- Open an issue on GitHub
- Check existing documentation
- Review troubleshooting section
- Check backend logs for errors

---

**Version:** 1.0.0  
**Last Updated:** 2025  
**Status:** Production Ready

Built with ❤️ for aerial image analysis

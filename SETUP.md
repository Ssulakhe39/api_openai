# Setup Guide

## Quick Start

### Option 1: Automated Setup (Recommended)

**Linux/Mac:**
```bash
chmod +x setup.sh
./setup.sh
```

**Windows:**
```cmd
setup.bat
```

### Option 2: Manual Setup

#### Backend Setup

1. Navigate to backend directory:
```bash
cd backend
```

2. Create Python virtual environment:
```bash
python3 -m venv venv
```

3. Activate virtual environment:
   - Linux/Mac: `source venv/bin/activate`
   - Windows: `venv\Scripts\activate`

4. Install dependencies:
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

5. Create necessary directories:
```bash
mkdir -p uploads masks static/images static/masks models/weights
```

6. Copy environment configuration:
```bash
cp .env.example .env
```

#### Frontend Setup

1. Navigate to frontend directory:
```bash
cd frontend
```

2. Install Node.js dependencies:
```bash
npm install
```

## Model Weights

Before running the application, you need to download the model weights:

### SAM2 (Segment Anything Model 2)
- Download from: [SAM2 GitHub](https://github.com/facebookresearch/segment-anything-2)
- Place checkpoint in: `backend/models/weights/sam2_checkpoint.pth`
- Update `SAM2_CHECKPOINT_PATH` in `backend/.env`

### YOLOv8
- The model will be automatically downloaded on first use
- Or manually download from: [Ultralytics](https://github.com/ultralytics/ultralytics)
- Place in: `backend/models/weights/yolov8n-seg.pt`

### U-Net
- Train your own model or download a pre-trained one
- Place in: `backend/models/weights/unet_buildings.pth`
- Update `UNET_MODEL_PATH` in `backend/.env`

## Running the Application

### Start Backend Server

```bash
cd backend
source venv/bin/activate  # Windows: venv\Scripts\activate
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

The backend API will be available at: http://localhost:8000

### Start Frontend Development Server

```bash
cd frontend
npm run dev
```

The frontend will be available at: http://localhost:3000

## Running Tests

### Backend Tests

```bash
cd backend
source venv/bin/activate  # Windows: venv\Scripts\activate
pytest
```

### Frontend Tests

```bash
cd frontend
npm test
```

## Troubleshooting

### Python Dependencies

If you encounter issues installing PyTorch or other dependencies:

1. Check your Python version (3.9+ required):
```bash
python --version
```

2. For GPU support, install PyTorch with CUDA:
```bash
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
```

3. For CPU-only (slower inference):
```bash
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
```

### Node.js Dependencies

If npm install fails:

1. Check Node.js version (18+ required):
```bash
node --version
```

2. Clear npm cache:
```bash
npm cache clean --force
```

3. Delete node_modules and reinstall:
```bash
rm -rf node_modules package-lock.json
npm install
```

### CORS Issues

If you encounter CORS errors:

1. Verify `CORS_ORIGINS` in `backend/.env` includes your frontend URL
2. Restart the backend server after changing `.env`

### Model Loading Issues

If models fail to load:

1. Verify model files exist in `backend/models/weights/`
2. Check file paths in `backend/.env`
3. Ensure sufficient disk space and RAM
4. Check logs for specific error messages

## Directory Structure

```
.
├── backend/
│   ├── api/              # FastAPI endpoints (to be implemented)
│   ├── models/           # Model adapters (to be implemented)
│   │   └── weights/      # Model checkpoint files (download separately)
│   ├── utils/            # Image processing utilities (to be implemented)
│   ├── tests/            # Backend tests
│   ├── uploads/          # Uploaded images (created at runtime)
│   ├── masks/            # Generated masks (created at runtime)
│   ├── static/           # Static file serving (created at runtime)
│   ├── .env              # Environment configuration (copy from .env.example)
│   ├── .env.example      # Example environment configuration
│   ├── pytest.ini        # Pytest configuration
│   └── requirements.txt  # Python dependencies
├── frontend/
│   ├── src/              # Frontend source code (to be implemented)
│   ├── public/           # Static assets
│   ├── tests/            # Frontend tests
│   ├── index.html        # Main HTML template
│   ├── package.json      # Node.js dependencies
│   ├── vite.config.js    # Vite configuration
│   └── jest.config.js    # Jest configuration
├── .gitignore            # Git ignore rules
├── README.md             # Project overview
├── SETUP.md              # This file
├── setup.sh              # Linux/Mac setup script
└── setup.bat             # Windows setup script
```

## Next Steps

After setup is complete:

1. ✅ Project structure created
2. ⏳ Implement backend image processing service (Task 2)
3. ⏳ Implement segmentation model architecture (Task 3)
4. ⏳ Implement backend API endpoints (Task 6)
5. ⏳ Implement frontend components (Tasks 9-12)
6. ⏳ Integration and testing (Tasks 14-17)

See `.kiro/specs/aerial-image-segmentation/tasks.md` for detailed implementation plan.

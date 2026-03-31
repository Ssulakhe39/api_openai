# Aerial Image Segmentation Web Application

A web application for segmenting buildings in aerial imagery using multiple deep learning models (SAM2, YOLOv8, U-Net).

## Project Structure

```
.
├── backend/
│   ├── api/          # FastAPI endpoints
│   ├── models/       # Segmentation model adapters
│   ├── utils/        # Image processing utilities
│   └── tests/        # Backend tests
├── frontend/
│   ├── src/          # Frontend source code
│   ├── public/       # Static assets
│   └── tests/        # Frontend tests
└── .kiro/
    └── specs/        # Project specifications
```

## Setup Instructions

### Backend Setup

1. Create and activate a Python virtual environment:
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Download model weights (instructions to be added)

4. Run the backend server:
```bash
uvicorn api.main:app --reload
```

### Frontend Setup

1. Install Node.js dependencies:
```bash
cd frontend
npm install
```

2. Run the development server:
```bash
npm run dev
```

3. Run tests:
```bash
npm test
```

## Features

- Upload aerial images (JPG, PNG, TIFF)
- Select from three segmentation models:
  - SAM2 (Segment Anything Model 2)
  - YOLOv8 Segmentation
  - U-Net
- View results in three panels:
  - Original image
  - Segmentation mask
  - Overlay visualization

## Requirements

- Python 3.9+
- Node.js 18+
- CUDA-capable GPU (recommended for model inference)

## Testing

### Backend Tests
```bash
cd backend
pytest
```

### Frontend Tests
```bash
cd frontend
npm test
```

## License

MIT

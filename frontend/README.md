# Aerial Image Segmentation - Frontend

Web-based frontend for the aerial image segmentation application. Upload aerial imagery, select AI models (SAM2, YOLOv8, U-Net), and visualize building segmentation results.

## Features

- **Image Upload**: Support for JPG, PNG, and TIFF formats (up to 50MB)
- **Model Selection**: Choose from three state-of-the-art segmentation models
- **Real-time Visualization**: View original image, segmentation mask, and overlay side-by-side
- **Interactive UI**: Visual feedback for all user interactions
- **Error Handling**: Clear error messages and graceful degradation

## Architecture

### Components

- **ImageUploader** (`src/imageUploader.js`): Handles file selection, validation, and upload
- **ModelSelector** (`src/modelSelector.js`): Manages model selection dropdown
- **SegmentationRunner** (`src/segmentationRunner.js`): Triggers segmentation and handles responses
- **VisualizationPanel** (`src/visualizationPanel.js`): Renders three-panel visualization with overlay
- **AppState** (`src/appState.js`): Manages application state and UI feedback
- **Main App** (`src/index.js`): Wires all components together

### Communication Flow

```
User Action → Component → API Call → Backend
                ↓
         State Update → Event → Other Components
                ↓
         UI Update (Visualization)
```

## Setup

### Prerequisites

- Node.js 16+ and npm
- Backend API running on http://localhost:8000

### Installation

```bash
cd frontend
npm install
```

### Development

Start the development server:

```bash
npm run dev
```

The app will be available at http://localhost:5173 (or the port shown in terminal).

### Build for Production

```bash
npm run build
```

Built files will be in the `dist/` directory.

### Preview Production Build

```bash
npm run preview
```

## Testing

Run all tests:

```bash
npm test
```

Run tests in watch mode:

```bash
npm test:watch
```

See [TESTING.md](./TESTING.md) for detailed testing instructions.

## API Integration

The frontend communicates with the backend API at `http://localhost:8000`:

- `POST /upload` - Upload image file
- `GET /models` - Get available models
- `POST /segment` - Run segmentation
- `GET /images/{filename}` - Serve uploaded images
- `GET /masks/{filename}` - Serve generated masks

## Browser Support

- Chrome/Edge 90+
- Firefox 88+
- Safari 14+

Requires Canvas API support for overlay generation.

## Configuration

Backend API URL can be changed in each component file (search for `http://localhost:8000`).

For production, consider using environment variables:

```javascript
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
```

## Troubleshooting

### CORS Errors

Ensure the backend has CORS configured for your frontend URL:

```python
allow_origins=[
    "http://localhost:5173",  # Vite default
    "http://localhost:3000",  # Alternative
]
```

### Images Not Loading

- Check that backend static file serving is configured
- Verify image/mask URLs are correct
- Check browser console for 404 errors

### Overlay Not Generating

- Ensure Canvas API is supported
- Check browser console for errors
- Verify mask image loads correctly

## Development Notes

- All components use vanilla JavaScript (no framework)
- Event-driven architecture using CustomEvents
- Modular design for easy testing and maintenance
- Follows design document specifications exactly

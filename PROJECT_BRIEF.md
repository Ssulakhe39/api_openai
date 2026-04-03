# BHUMI AI — Project Brief

## What This Is

A full-stack web application for automated building detection and boundary extraction from aerial/drone/satellite imagery. Users upload images, run AI segmentation using trained deep learning models, review detected building polygons, and export results. Supports both single-image and batch (ZIP) workflows.

**Live app:** Frontend on `http://localhost:4000`, Backend API on `http://localhost:8000`.

---

## Tech Stack

| Layer | Technology | Notes |
|-------|-----------|-------|
| Backend framework | **FastAPI** (Python) | Single-file API at `backend/api/main.py` (~1070 lines) |
| ML inference | **PyTorch 2.x**, **Ultralytics (YOLOv8)**, **torchvision (Mask R-CNN)** | Lazy-loaded on first segmentation request |
| Image processing | **OpenCV**, **Pillow**, **NumPy**, **scikit-image** | Boundary detection, morphological ops, contour extraction |
| Frontend | **Vanilla JS (ES6+)** with **Vite 5** as dev server/bundler | No framework — plain modules, Canvas API for overlays |
| Styling | **CSS3** with CSS variables | Dark/light theme system via `theme.css` + `app.css` |
| Dev server proxy | Vite proxies `/api`, `/upload`, `/segment`, `/boundaries`, `/images`, `/masks`, `/models` → `localhost:8000` | Configured in `frontend/vite.config.js` |

---

## Current Folder Structure (Post-Cleanup)

```
.
├── README.md                          # Project overview (the only doc at root)
├── backend/
│   ├── api/
│   │   ├── __init__.py
│   │   └── main.py                    # THE FastAPI app — all endpoints, models, state
│   ├── models/
│   │   ├── __init__.py                # Lazy imports for adapters
│   │   ├── segmentation_model.py      # ABC: load/preprocess/predict/postprocess/segment
│   │   ├── segmentation_model_manager.py  # Registry + lazy loader for all models
│   │   ├── yolov8_adapter.py          # YOLOv8m-seg instance segmentation
│   │   ├── maskrcnn_adapter.py        # Mask R-CNN (ResNet50-FPN) instance segmentation
│   │   ├── sam2_adapter.py            # SAM2 adapter (requires sam2 package)
│   │   ├── unet_adapter.py            # U-Net semantic segmentation
│   │   ├── sam2_hiera_l.yaml          # SAM2 model config
│   │   └── weights/                   # .gitignored — model weight files go here
│   │       ├── best_fixed.pt          # YOLOv8m-seg trained on building dataset (~109MB)
│   │       └── maskrcnn_building_best.pth  # Mask R-CNN trained on building dataset (~176MB)
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── image_processor.py         # Validate, load, save images/masks, base64 encoding
│   │   ├── boundary_detector.py       # OpenCV morphological + contour-based boundary detection
│   │   └── gpt_boundary.py            # minAreaRect per-instance boundary extraction
│   ├── tests/                         # pytest suite (14 test files)
│   ├── backend/uploads/               # ⚠️ NESTED — runtime uploads land here (see issues below)
│   ├── .env / .env.example
│   ├── requirements.txt
│   ├── run_server.py                  # uvicorn launcher
│   └── pytest.ini
├── frontend/
│   ├── index.html                     # SPA shell — sidebar nav, all page sections
│   ├── vite.config.js                 # Dev server on port 4000, proxy rules
│   ├── package.json                   # Deps: vite, jest, fast-check
│   ├── jest.config.js
│   ├── public/
│   │   ├── logo.png
│   │   └── logo.svg
│   ├── src/
│   │   ├── index.js                   # BhumiAIApp — SPA controller, page routing, component init
│   │   ├── appState.js                # Centralized state: uploaded image, model, results, errors
│   │   ├── imageUploader.js           # File validation + POST /upload
│   │   ├── modelSelector.js           # GET /models + card-based selection UI
│   │   ├── segmentationRunner.js      # POST /segment + loading state
│   │   ├── visualizationPanel.js      # Three-panel display: original / mask / overlay (Canvas API)
│   │   ├── boundaryDetector.js        # POST /boundaries — OpenCV contour UI
│   │   ├── gptBoundaryDetector.js     # POST /api/gpt-boundaries — enhanced boundary UI
│   │   ├── batchProcessor.js          # ZIP upload + batch run + progress polling
│   │   ├── batchPolygonEditor.js      # Per-image polygon editor (canvas drawing)
│   │   ├── dashboard.js               # Stats cards, recent jobs, system status
│   │   ├── theme.css                  # Design system: CSS variables, dark/light tokens
│   │   ├── app.css                    # Layout-specific styles (sidebar, pages, cards)
│   │   └── styles.css                 # Legacy styles (partially overlaps with theme.css)
│   └── tests/                         # Empty — no automated frontend tests yet
└── .kiro/ / .vscode/                  # IDE config
```

---

## Backend API Endpoints

### Core
| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/` | API info |
| `GET` | `/health` | Health check → `{"status": "healthy"}` |
| `GET` | `/models` | List available models (currently YOLOv8m-custom, maskrcnn-custom) |

### Auth (removed)
Auth endpoints, USERS dict, login.html, and all sessionStorage token logic have been removed. The app is open-access.

### Single Image Processing
| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/upload` | Upload image (multipart), validate, save, return `image_id` + dimensions |
| `POST` | `/segment` | Run segmentation with chosen model, return mask (base64 + URL) |
| `POST` | `/boundaries` | OpenCV contour-based boundary detection on existing mask |
| `POST` | `/api/gpt-boundaries` | Per-instance minAreaRect boundary extraction + overlay |

### Batch Processing (in-memory state)
| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/api/batch/upload-zip` | Upload ZIP (max 500MB, 50 images), extract, create batch job |
| `POST` | `/api/batch/{id}/run` | Start background sequential processing |
| `GET` | `/api/batch/{id}/status` | Poll progress (pending/processing/done/failed per item) |
| `GET` | `/api/batch/{id}/items/{item_id}/image` | Serve original image for a batch item |
| `POST` | `/api/batch/{id}/items/{item_id}/polygons` | Save edited polygons |
| `POST` | `/api/batch/{id}/items/{item_id}/retry` | Retry a failed item |
| `GET` | `/api/batch/{id}/download?format=json\|png\|jpeg` | Download results as ZIP |

### Static File Serving
- `/images/{filename}` → `backend/uploads/images/`
- `/masks/{filename}` → `backend/uploads/masks/`

---

## ML Models

| Model | Adapter | Weight File | Architecture | Output |
|-------|---------|-------------|-------------|--------|
| `yolov8m-custom` | `YOLOv8Adapter` | `weights/best_fixed.pt` (109MB) | YOLOv8m-seg (Ultralytics) | Instance masks → combined binary mask |
| `maskrcnn-custom` | `MaskRCNNAdapter` | `weights/maskrcnn_building_best.pth` (176MB) | Mask R-CNN ResNet50-FPN (torchvision) | Instance masks → combined binary mask |
| `sam2` | `SAM2Adapter` | Not present | SAM2 Hiera-L | Auto mask generation (requires `segment-anything-2` package) |
| `unet` | `UNetAdapter` | Not present | Custom U-Net (PyTorch) | Semantic segmentation |

Only YOLOv8 and Mask R-CNN are currently functional with weights present. SAM2 and U-Net adapters exist but have no weight files.

All adapters implement the `SegmentationModel` ABC: `load()` → `preprocess()` → `predict()` → `postprocess()` → `segment()`. Both YOLOv8 and Mask R-CNN also expose `instance_segment()` returning per-building masks.

---

## Frontend Pages (SPA)

All pages live in `index.html` as `<div id="page-{name}" class="page-section">` blocks, toggled by `index.js`.

| Page | Sidebar Label | Key Components |
|------|--------------|----------------|
| `single` | Single Processing | ImageUploader, ModelSelector, SegmentationRunner, VisualizationPanel, BoundaryDetector, GPTBoundaryDetector |
| `batch` | Batch Processing | BatchProcessor (ZIP upload, progress, grid), BatchPolygonEditor |
| `dashboard` | Dashboard | Stats cards, recent jobs, system status |
| `settings` | Settings/Profile | Theme toggle, default model/format prefs, user profile |

Login is not required — the app is open-access.

---

## How to Run

```bash
# Backend (from project root)
cd backend
source venv/bin/activate
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload

# Frontend (from project root, separate terminal)
cd frontend
npm run dev
```

Open `http://localhost:4000` in browser. Vite proxies API calls to the backend.

---

## Known Issues & Technical Debt

### Critical / Structural
1. **Monolithic `main.py`** (~1070 lines) — All endpoints, Pydantic models, batch state, error handlers, and business logic in one file. Should be split into routers (`auth.py`, `segmentation.py`, `batch.py`, `boundaries.py`) with separate schema files.

2. **Nested upload directory** — Code creates `backend/uploads/images/` (relative to CWD), but when run from `backend/`, this creates `backend/backend/uploads/`. The `UPLOAD_DIR`, `MASK_DIR`, `BATCH_DIR` paths at the top of `main.py` use `Path("backend/uploads/...")` which assumes CWD is the project root, not `backend/`. This is fragile and confusing.

3. **In-memory batch state** — `batch_jobs: dict` lives in process memory. Server restart loses all batch job state. No persistence layer.

4. ~~**In-memory auth**~~ — Removed.

5. ~~**No auth middleware**~~ — Removed (auth eliminated entirely).

### Backend Code Quality
6. **Duplicate `import cv2`** — cv2 is imported at module level AND re-imported inside multiple endpoint functions.

7. **`import json` inside function** — `download_batch()` imports `json` inside the function body instead of at the top.

8. ~~**`import secrets` mid-file**~~ — Removed with auth.

9. **Hardcoded model list in `/models` endpoint** — The `get_models()` endpoint returns a hardcoded list instead of querying `model_manager.get_available_models()`.

10. **No request validation middleware** — File size is checked by reading the entire file into memory first (`contents = await file.read()`), which means a 500MB upload is fully buffered before rejection.

11. **`run_server.py` has `reload=False`** — The standalone runner disables reload, but the recommended command uses `--reload`. Inconsistent.

### Frontend Code Quality
12. **Three CSS files** — `theme.css` (design system), `app.css` (layout), `styles.css` (legacy). `styles.css` partially overlaps with the other two and should be consolidated.

13. **No automated tests** — `frontend/tests/` is empty. Jest + fast-check are installed but unused.

14. ~~**`login.html` is separate**~~ — Removed.

### Configuration
15. **`.env.example` references wrong paths** — Lists `SAM2_CHECKPOINT_PATH`, `YOLOV8_MODEL_PATH`, `UNET_MODEL_PATH` but the code doesn't read these env vars. Model paths are hardcoded in `segmentation_model_manager.py`.

16. **CORS origins list is excessive** — 8 hardcoded origins for localhost variants. Could use a wildcard pattern or env-driven config.

---

## Recommended Refactoring Priority

### Phase 1: Backend Structure (High Impact)
- Split `main.py` into FastAPI routers: `routers/segmentation.py`, `routers/batch.py`, `routers/boundaries.py`
- Extract Pydantic schemas to `schemas/` directory
- Fix upload directory paths to be relative to `backend/` (use `Path(__file__).parent.parent`)
- Move all imports to top of files
- Make `/models` endpoint dynamic from model manager

### Phase 2: Configuration & Reliability
- Read model paths from `.env` instead of hardcoding
- Add request size limits at the ASGI level (not by reading full body)

### Phase 3: Frontend Cleanup
- Consolidate CSS into `theme.css` + `app.css`, remove `styles.css`
- Add basic Jest tests for core components

### Phase 4: Persistence & Production Readiness
- Add SQLite/PostgreSQL for batch job state and user accounts
- Add proper file cleanup (scheduled deletion of old uploads)
- Dockerize the application

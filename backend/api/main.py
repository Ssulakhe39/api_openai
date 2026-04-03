"""
FastAPI application for aerial image segmentation.

This module sets up the FastAPI application instance, configures CORS middleware
for frontend communication, and sets up static file serving for images and masks.
"""

from fastapi import FastAPI, UploadFile, File, HTTPException, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel
from enum import Enum
import os
import uuid
import time
import logging
import zipfile
import io
import asyncio
import shutil
from datetime import datetime, timezone
from pathlib import Path
import base64
import numpy as np
import cv2

# Load .env file from the backend directory
try:
    from dotenv import load_dotenv
    # Try both relative and absolute paths
    _env_path = Path(".env")
    if not _env_path.exists():
        _env_path = Path(__file__).parent.parent / ".env"
    load_dotenv(dotenv_path=_env_path, override=True)
except ImportError:
    pass  # python-dotenv not installed, rely on OS env vars

from utils.image_processor import ImageProcessor
from models.segmentation_model_manager import SegmentationModelManager
from utils.boundary_detector import BoundaryDetector
from utils.gpt_boundary import GPTBoundaryExtractor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app instance
app = FastAPI(
    title="Aerial Image Segmentation API",
    description="API for segmenting buildings in aerial/satellite imagery using SAM2, YOLOv8, and U-Net models",
    version="1.0.0"
)

# Configure CORS middleware for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # React/Vite dev server
        "http://localhost:3001",  # Vite fallback port
        "http://localhost:4000",  # Vite port (deployment)
        "http://localhost:5173",  # Vite default port
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "http://127.0.0.1:4000",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

# Create directories for storing uploaded images and generated masks
UPLOAD_DIR = Path("backend/uploads/images")
MASK_DIR = Path("backend/uploads/masks")
BATCH_DIR = Path("backend/uploads/batch")

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
MASK_DIR.mkdir(parents=True, exist_ok=True)
BATCH_DIR.mkdir(parents=True, exist_ok=True)

# Mount static file directories for serving images and masks
app.mount("/images", StaticFiles(directory=str(UPLOAD_DIR)), name="images")
app.mount("/masks", StaticFiles(directory=str(MASK_DIR)), name="masks")


# Error response model
class ErrorResponse(BaseModel):
    """Standard error response format."""
    detail: str
    timestamp: str
    path: str = ""


# Exception handlers
@app.exception_handler(400)
async def bad_request_handler(request: Request, exc: HTTPException):
    """Handle 400 Bad Request errors."""
    logger.warning(f"Bad request: {exc.detail} - Path: {request.url.path}")
    return JSONResponse(
        status_code=400,
        content=ErrorResponse(
            detail=exc.detail,
            timestamp=datetime.now(timezone.utc).isoformat(),
            path=str(request.url.path)
        ).model_dump()
    )


@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException):
    """Handle 404 Not Found errors."""
    logger.warning(f"Resource not found: {exc.detail} - Path: {request.url.path}")
    return JSONResponse(
        status_code=404,
        content=ErrorResponse(
            detail=exc.detail,
            timestamp=datetime.now(timezone.utc).isoformat(),
            path=str(request.url.path)
        ).model_dump()
    )


@app.exception_handler(413)
async def payload_too_large_handler(request: Request, exc: HTTPException):
    """Handle 413 Payload Too Large errors."""
    logger.warning(f"Payload too large: {exc.detail} - Path: {request.url.path}")
    return JSONResponse(
        status_code=413,
        content=ErrorResponse(
            detail=exc.detail,
            timestamp=datetime.now(timezone.utc).isoformat(),
            path=str(request.url.path)
        ).model_dump()
    )


@app.exception_handler(500)
async def internal_server_error_handler(request: Request, exc: Exception):
    """Handle 500 Internal Server Error."""
    logger.error(f"Internal server error: {str(exc)} - Path: {request.url.path}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            detail="Internal server error. Please try again later.",
            timestamp=datetime.now(timezone.utc).isoformat(),
            path=str(request.url.path)
        ).model_dump()
    )


@app.get("/")
async def root():
    """Root endpoint to verify API is running."""
    return {
        "message": "Aerial Image Segmentation API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

# Simple hardcoded credentials — replace with a DB-backed solution for production
USERS = {
    "admin": "admin123",
    "user":  "user123",
}

import secrets

class LoginRequest(BaseModel):
    username: str
    password: str

@app.post("/api/auth/login")
async def login(request: LoginRequest):
    pwd = USERS.get(request.username)
    if not pwd or pwd != request.password:
        raise HTTPException(status_code=401, detail="Invalid username or password.")
    token = secrets.token_hex(32)
    return {"token": token, "username": request.username}


class RegisterRequest(BaseModel):
    username: str
    password: str

@app.post("/api/auth/register")
async def register(request: RegisterRequest):
    if not request.username or len(request.username) < 3:
        raise HTTPException(status_code=400, detail="Username must be at least 3 characters.")
    if not request.password or len(request.password) < 4:
        raise HTTPException(status_code=400, detail="Password must be at least 4 characters.")
    if request.username in USERS:
        raise HTTPException(status_code=409, detail="Username already exists.")
    USERS[request.username] = request.password
    token = secrets.token_hex(32)
    logger.info(f"New user registered: {request.username}")
    return {"token": token, "username": request.username}


# Response models
class UploadResponse(BaseModel):
    """Response model for image upload."""
    image_id: str
    image_url: str
    width: int
    height: int


class SegmentRequest(BaseModel):
    """Request model for segmentation."""
    image_id: str
    model: str


class SegmentResponse(BaseModel):
    """Response model for segmentation."""
    mask_url: str
    mask_base64: str
    processing_time: float
    model_used: str


class ModelInfo(BaseModel):
    """Information about a segmentation model."""
    name: str
    display_name: str
    description: str


class ModelsResponse(BaseModel):
    """Response model for available models."""
    models: list[ModelInfo]


# Initialize ImageProcessor
image_processor = ImageProcessor()

# Initialize SegmentationModelManager
model_manager = SegmentationModelManager()

# Initialize BoundaryDetector with GIS-ready parameters
boundary_detector = BoundaryDetector(
    min_area=50,              # Minimum building area in pixels
    epsilon_factor=0.01,      # 1% Douglas-Peucker simplification
    morph_kernel_size=3,      # 3x3 morphological kernel
    morph_iterations=2,       # 2 iterations for closing/opening
    shapely_tolerance=None    # Optional Shapely simplification (disabled)
)

# ---------------------------------------------------------------------------
# Batch processing models and state
# ---------------------------------------------------------------------------

class ItemStatus(str, Enum):
    pending = "pending"
    processing = "processing"
    done = "done"
    failed = "failed"

class JobStatus(str, Enum):
    uploaded = "uploaded"
    running = "running"
    complete = "complete"
    failed = "failed"

class BatchItem(BaseModel):
    item_id: str
    original_filename: str
    image_path: str = ""
    mask_path: str = ""
    status: ItemStatus = ItemStatus.pending
    error: str = ""
    polygons: list = []
    building_count: int = 0

class BatchJob(BaseModel):
    batch_id: str
    status: JobStatus = JobStatus.uploaded
    model: str = ""
    items: list[BatchItem] = []
    created_at: str = ""

class BatchUploadResponse(BaseModel):
    batch_id: str
    filenames: list[str]
    total: int

class BatchRunRequest(BaseModel):
    model: str

class BatchStatusResponse(BaseModel):
    batch_id: str
    status: str
    total: int
    done: int
    failed: int
    pending: int
    processing: int
    items: list[BatchItem]

# In-memory batch store
batch_jobs: dict[str, BatchJob] = {}

MAX_BATCH_ZIP_SIZE = 500 * 1024 * 1024  # 500 MB
MAX_BATCH_IMAGES = 50
SUPPORTED_IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".tiff", ".tif"}

# Maximum file size: 50MB
MAX_FILE_SIZE = 50 * 1024 * 1024

# Segmentation timeout: 300 seconds (5 minutes)
SEGMENTATION_TIMEOUT = 300


@app.post("/upload", response_model=UploadResponse)
async def upload_image(file: UploadFile = File(...)):
    """
    Upload an aerial image for segmentation.
    
    Accepts multipart/form-data file upload, validates the file format,
    generates a unique image_id, saves the file to storage, and returns
    metadata about the uploaded image.
    
    Args:
        file: Uploaded image file (JPG, PNG, or TIFF)
        
    Returns:
        UploadResponse with image_id, image_url, width, and height
        
    Raises:
        HTTPException 400: Invalid file format or corrupted file
        HTTPException 413: File too large
        HTTPException 500: Server error during processing
    """
    logger.info(f"Upload request received: filename={file.filename}")
    
    # Check file size
    contents = await file.read()
    file_size = len(contents)
    
    if file_size > MAX_FILE_SIZE:
        logger.warning(f"File too large: {file_size} bytes (max: {MAX_FILE_SIZE})")
        raise HTTPException(
            status_code=413,
            detail="Image file is too large. Maximum size is 50MB."
        )
    
    # Generate unique image_id
    image_id = str(uuid.uuid4())
    
    # Get file extension from original filename
    original_filename = file.filename or "image.jpg"
    file_extension = Path(original_filename).suffix.lower()
    
    # Validate file extension
    if file_extension not in ImageProcessor.SUPPORTED_FORMATS:
        logger.warning(f"Unsupported format: {file_extension}")
        raise HTTPException(
            status_code=400,
            detail="Unsupported file format. Please upload JPG, PNG, or TIFF images."
        )
    
    # Save uploaded file temporarily
    temp_file_path = UPLOAD_DIR / f"{image_id}{file_extension}"
    
    try:
        # Write file contents
        with open(temp_file_path, "wb") as f:
            f.write(contents)
        
        logger.info(f"File saved: image_id={image_id}, size={file_size} bytes")
        
        # Validate image integrity
        validation_result = image_processor.validate_image(str(temp_file_path))
        if not validation_result.valid:
            # Remove invalid file
            temp_file_path.unlink()
            logger.warning(f"Invalid image: image_id={image_id}, error={validation_result.error}")
            raise HTTPException(
                status_code=400,
                detail=validation_result.error
            )
        
        # Load image to get dimensions
        image_array = image_processor.load_image(str(temp_file_path))
        height, width = image_array.shape[:2]
        
        # Construct image URL
        image_url = f"/images/{image_id}{file_extension}"
        
        logger.info(f"Upload successful: image_id={image_id}, dimensions={width}x{height}")
        
        return UploadResponse(
            image_id=image_id,
            image_url=image_url,
            width=width,
            height=height
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Clean up file on error
        if temp_file_path.exists():
            temp_file_path.unlink()
        logger.error(f"Upload failed: image_id={image_id}, error={str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process uploaded image: {str(e)}"
        )



@app.post("/segment", response_model=SegmentResponse)
async def segment_image(request: SegmentRequest):
    """
    Run segmentation on an uploaded image.
    
    Accepts a SegmentRequest with image_id and model name, validates both,
    loads the image, runs segmentation using the specified model, saves the
    mask, and returns the mask data with processing time.
    
    Args:
        request: SegmentRequest containing image_id and model name
        
    Returns:
        SegmentResponse with mask_url, mask_base64, processing_time, and model_used
        
    Raises:
        HTTPException 400: Invalid model name
        HTTPException 404: Image not found
        HTTPException 500: Segmentation failed
    """
    logger.info(f"Segmentation request: image_id={request.image_id}, model={request.model}")
    
    # Validate model name is supported
    available_models = model_manager.get_available_models()
    if request.model not in available_models:
        logger.warning(f"Invalid model: {request.model}")
        raise HTTPException(
            status_code=400,
            detail=f"Invalid model name. Supported models: {', '.join(available_models)}"
        )
    
    # Find the uploaded image file
    image_path = None
    for ext in ImageProcessor.SUPPORTED_FORMATS:
        potential_path = UPLOAD_DIR / f"{request.image_id}{ext}"
        if potential_path.exists():
            image_path = potential_path
            break
    
    # Validate image_id exists
    if image_path is None:
        logger.warning(f"Image not found: image_id={request.image_id}")
        raise HTTPException(
            status_code=404,
            detail="Image not found. Please upload an image first."
        )
    
    try:
        # Load image using ImageProcessor
        logger.info(f"Loading image: {image_path}")
        image_array = image_processor.load_image(str(image_path))
        
        # Run segmentation using SegmentationModelManager
        logger.info(f"Starting segmentation: model={request.model}, image_shape={image_array.shape}")
        start_time = time.time()
        
        # Note: In production, you would want to implement actual timeout handling
        # using asyncio.wait_for or similar mechanism. For now, we log the timeout value.
        mask = model_manager.segment(image_array, request.model)
        
        processing_time = time.time() - start_time
        logger.info(f"Segmentation completed: time={processing_time:.2f}s")
        
        # Check if processing took too long (warning only, not enforced)
        if processing_time > SEGMENTATION_TIMEOUT:
            logger.warning(
                f"Segmentation exceeded timeout: "
                f"time={processing_time:.2f}s, timeout={SEGMENTATION_TIMEOUT}s"
            )
        
        # Save mask
        mask_filename = f"{request.image_id}-{request.model}-mask.png"
        mask_path = MASK_DIR / mask_filename
        image_processor.save_mask(mask, str(mask_path))
        logger.info(f"Mask saved: {mask_path}")
        
        # Convert to base64
        mask_base64 = image_processor.mask_to_base64(mask)
        
        # Construct mask URL
        mask_url = f"/masks/{mask_filename}"
        
        logger.info(
            f"Segmentation successful: image_id={request.image_id}, "
            f"model={request.model}, time={processing_time:.2f}s"
        )
        
        return SegmentResponse(
            mask_url=mask_url,
            mask_base64=mask_base64,
            processing_time=processing_time,
            model_used=request.model
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(
            f"Segmentation failed: image_id={request.image_id}, "
            f"model={request.model}, error={str(e)}",
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail=f"Segmentation failed. The image may be incompatible with this model: {str(e)}"
        )


@app.get("/models", response_model=ModelsResponse)
async def get_models():
    """
    Get list of available segmentation models.
    
    Returns information about all available models including their name,
    display name, and description.
    
    Returns:
        ModelsResponse containing list of ModelInfo objects
    """
    models = [
        ModelInfo(
            name="yolov8m-custom",
            display_name="YOLOv8m Custom (Your Dataset)",
            description="YOLOv8m trained on your building dataset - Fixed version"
        ),
        ModelInfo(
            name="maskrcnn-custom",
            display_name="Mask R-CNN Custom (Your Dataset)",
            description="Mask R-CNN trained on your building dataset"
        )
    ]
    
    return ModelsResponse(models=models)



class BoundaryRequest(BaseModel):
    """Request model for boundary detection."""
    image_id: str
    model: str


class BoundaryResponse(BaseModel):
    """Response model for boundary detection."""
    buildings: list
    total_buildings: int
    processing_time: float


@app.post("/boundaries", response_model=BoundaryResponse)
async def detect_boundaries(request: BoundaryRequest):
    """
    Detect building boundaries from segmentation mask.
    
    Extracts building contours from the segmentation mask and returns
    polygon coordinates for each detected building.
    
    Args:
        request: BoundaryRequest with image_id and model name
        
    Returns:
        BoundaryResponse with list of buildings and their coordinates
        
    Raises:
        HTTPException 404: Mask not found
        HTTPException 500: Boundary detection failed
    """
    logger.info(f"Boundary detection request: image_id={request.image_id}, model={request.model}")
    
    # Find the mask file
    mask_filename = f"{request.image_id}-{request.model}-mask.png"
    mask_path = MASK_DIR / mask_filename
    
    if not mask_path.exists():
        logger.warning(f"Mask not found: {mask_path}")
        raise HTTPException(
            status_code=404,
            detail="Mask not found. Please run segmentation first."
        )
    
    try:
        import cv2
        # Load mask
        logger.info(f"Loading mask: {mask_path}")
        mask = image_processor.load_image(str(mask_path))
        
        # Convert to grayscale if needed
        if len(mask.shape) == 3:
            mask = cv2.cvtColor(mask, cv2.COLOR_RGB2GRAY)
        
        # Detect boundaries
        logger.info("Detecting building boundaries...")
        start_time = time.time()
        
        buildings = boundary_detector.detect_boundaries(mask)
        
        processing_time = time.time() - start_time
        logger.info(f"Boundary detection completed: {len(buildings)} buildings found, time={processing_time:.2f}s")
        
        return BoundaryResponse(
            buildings=buildings,
            total_buildings=len(buildings),
            processing_time=processing_time
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Boundary detection failed: image_id={request.image_id}, "
            f"model={request.model}, error={str(e)}",
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail=f"Boundary detection failed: {str(e)}"
        )


# ---------------------------------------------------------------------------
# GPT-4o Vision boundary extraction
# ---------------------------------------------------------------------------

class GPTBoundaryRequest(BaseModel):
    """Request model for GPT-4o boundary detection."""
    image_id: str
    model: str  # yolov8m-custom | maskrcnn-custom | sam2


class GPTBoundaryResponse(BaseModel):
    """Response model for GPT-4o boundary detection."""
    gpt_overlay_b64: str
    opencv_overlay_b64: str
    building_count: int
    polygons: list
    processing_time_s: float
    fallback_count: int
    gpt_count: int = 0
    fallback_reasons: dict = {}
    image_url: str = ""


def _opencv_overlay(original_bgr: np.ndarray, mask_gray: np.ndarray) -> np.ndarray:
    """Draw OpenCV contours on original image (green, 2px)."""
    import cv2 as _cv2
    result = original_bgr.copy()
    contours, _ = _cv2.findContours(mask_gray, _cv2.RETR_EXTERNAL, _cv2.CHAIN_APPROX_SIMPLE)
    _cv2.drawContours(result, contours, -1, (0, 255, 0), 2)
    return result


@app.post("/api/gpt-boundaries", response_model=GPTBoundaryResponse)
async def gpt_boundaries(request: GPTBoundaryRequest):
    """
    Detect building boundaries using GPT-4o Vision per-instance masks.

    Accepts image_id + model, runs instance segmentation, sends each
    building crop to GPT-4o, and returns colour-filled overlay + polygons.
    """
    api_key = os.getenv("OPENAI_API_KEY", "")
    # api_key kept for interface compatibility but not used

    # Find original image
    original_path = None
    for ext in ImageProcessor.SUPPORTED_FORMATS:
        p = UPLOAD_DIR / f"{request.image_id}{ext}"
        if p.exists():
            original_path = p
            break
    if original_path is None:
        raise HTTPException(status_code=404, detail="Original image not found.")

    # Find existing mask (must have run /segment first)
    mask_filename = f"{request.image_id}-{request.model}-mask.png"
    mask_path = MASK_DIR / mask_filename
    if not mask_path.exists():
        raise HTTPException(status_code=404, detail="Mask not found. Please run segmentation first.")

    try:
        import cv2
        start_time = time.time()

        # Load original image in BGR for OpenCV
        original_rgb = image_processor.load_image(str(original_path))
        original_bgr = cv2.cvtColor(original_rgb, cv2.COLOR_RGB2BGR)

        # Load combined mask (grayscale)
        mask_rgb = image_processor.load_image(str(mask_path))
        if len(mask_rgb.shape) == 3:
            mask_gray = cv2.cvtColor(mask_rgb, cv2.COLOR_RGB2GRAY)
        else:
            mask_gray = mask_rgb

        # Get per-instance masks from the model
        model_obj = model_manager.get_model(request.model)
        if hasattr(model_obj, 'instance_segment'):
            instance_masks = model_obj.instance_segment(original_rgb)
        else:
            # Fallback: treat combined mask as single instance
            instance_masks = [mask_gray]

        logger.info(f"GPT boundaries: {len(instance_masks)} instance masks for model={request.model}")

        # Run GPT boundary extraction
        extractor = GPTBoundaryExtractor(api_key=api_key)
        result = await extractor.process_async(original_bgr, instance_masks)

        # OpenCV overlay for comparison
        opencv_img = _opencv_overlay(original_bgr, mask_gray)

        # Encode both overlays as base64
        _, gpt_buf = cv2.imencode(".png", result["gpt_overlay_bgr"])
        gpt_b64 = base64.b64encode(gpt_buf.tobytes()).decode("utf-8")

        _, cv_buf = cv2.imencode(".png", opencv_img)
        cv_b64 = base64.b64encode(cv_buf.tobytes()).decode("utf-8")

        processing_time = time.time() - start_time
        logger.info(
            f"GPT boundaries done: {len(result['polygons'])} buildings, "
            f"{result['fallback_count']} fallbacks, {processing_time:.1f}s"
        )

        return GPTBoundaryResponse(
            gpt_overlay_b64=gpt_b64,
            opencv_overlay_b64=cv_b64,
            building_count=len(result["polygons"]),
            polygons=result["polygons"],
            processing_time_s=round(processing_time, 2),
            fallback_count=result["fallback_count"],
            gpt_count=result.get("gpt_count", 0),
            fallback_reasons=result.get("fallback_reasons", {}),
            image_url=f"/images/{request.image_id}{original_path.suffix}",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"GPT boundary detection failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"GPT boundary detection failed: {str(e)}")


# ---------------------------------------------------------------------------
# Batch endpoints
# ---------------------------------------------------------------------------

@app.get("/api/batch/{batch_id}/items/{item_id}/image")
async def get_batch_item_image(batch_id: str, item_id: str):
    """Serve the original image for a batch item."""
    from fastapi.responses import FileResponse
    job = batch_jobs.get(batch_id)
    if not job:
        raise HTTPException(status_code=404, detail="Batch job not found.")
    item = next((i for i in job.items if i.item_id == item_id), None)
    if not item or not item.image_path:
        raise HTTPException(status_code=404, detail="Item image not found.")
    p = Path(item.image_path)
    if not p.exists():
        raise HTTPException(status_code=404, detail="Image file not found.")
    return FileResponse(str(p))


@app.post("/api/batch/upload-zip", response_model=BatchUploadResponse)
async def upload_zip(file: UploadFile = File(...)):
    """Upload a ZIP of images for batch processing."""
    # Validate extension
    if not (file.filename or "").lower().endswith(".zip"):
        raise HTTPException(status_code=400, detail="Only .zip files are accepted.")

    contents = await file.read()
    if len(contents) > MAX_BATCH_ZIP_SIZE:
        raise HTTPException(status_code=413, detail="ZIP file exceeds 500 MB limit.")

    # Validate it's a real zip
    if not zipfile.is_zipfile(io.BytesIO(contents)):
        raise HTTPException(status_code=400, detail="Uploaded file is not a valid ZIP archive.")

    batch_id = str(uuid.uuid4())
    batch_img_dir = BATCH_DIR / batch_id / "images"
    batch_img_dir.mkdir(parents=True, exist_ok=True)

    items: list[BatchItem] = []
    with zipfile.ZipFile(io.BytesIO(contents)) as zf:
        image_members = [
            m for m in zf.namelist()
            if Path(m).suffix.lower() in SUPPORTED_IMAGE_EXTS and not m.startswith("__MACOSX")
        ]
        if not image_members:
            shutil.rmtree(BATCH_DIR / batch_id, ignore_errors=True)
            raise HTTPException(status_code=400, detail="ZIP contains no supported image files (jpg, jpeg, png, tiff, tif).")
        if len(image_members) > MAX_BATCH_IMAGES:
            shutil.rmtree(BATCH_DIR / batch_id, ignore_errors=True)
            raise HTTPException(status_code=400, detail=f"ZIP contains more than {MAX_BATCH_IMAGES} images.")

        for member in image_members:
            item_id = str(uuid.uuid4())
            original_filename = Path(member).name
            dest = batch_img_dir / f"{item_id}{Path(member).suffix.lower()}"
            dest.write_bytes(zf.read(member))
            items.append(BatchItem(
                item_id=item_id,
                original_filename=original_filename,
                image_path=str(dest),
            ))

    job = BatchJob(
        batch_id=batch_id,
        status=JobStatus.uploaded,
        items=items,
        created_at=datetime.now(timezone.utc).isoformat(),
    )
    batch_jobs[batch_id] = job
    logger.info(f"Batch uploaded: batch_id={batch_id}, images={len(items)}")
    return BatchUploadResponse(batch_id=batch_id, filenames=[i.original_filename for i in items], total=len(items))


async def _run_batch_job(batch_id: str):
    """Background task: sequentially segment + detect boundaries for each item using GPT-4o Vision."""
    job = batch_jobs.get(batch_id)
    if not job:
        return

    batch_mask_dir = BATCH_DIR / batch_id / "masks"
    batch_mask_dir.mkdir(parents=True, exist_ok=True)

    api_key = os.getenv("OPENAI_API_KEY", "")
    extractor = GPTBoundaryExtractor(api_key=api_key)

    for item in job.items:
        item.status = ItemStatus.processing
        try:
            import cv2
            img_path = Path(item.image_path)
            image_array = image_processor.load_image(str(img_path))
            original_bgr = cv2.cvtColor(image_array, cv2.COLOR_RGB2BGR)

            # Segmentation
            mask = model_manager.segment(image_array, job.model)
            mask_filename = f"{item.item_id}-mask.png"
            mask_path = batch_mask_dir / mask_filename
            image_processor.save_mask(mask, str(mask_path))
            item.mask_path = str(mask_path)

            # Get per-instance masks from the model
            mask_gray = mask if len(mask.shape) == 2 else cv2.cvtColor(mask, cv2.COLOR_RGB2GRAY)
            model_obj = model_manager.get_model(job.model)
            if hasattr(model_obj, 'instance_segment'):
                instance_masks = model_obj.instance_segment(image_array)
            else:
                # Fallback: treat combined mask as single instance
                instance_masks = [mask_gray]

            # GPT boundary detection
            result = await extractor.process_async(original_bgr, instance_masks)
            item.polygons = result["polygons"]
            item.building_count = len(result["polygons"])
            item.status = ItemStatus.done
            logger.info(f"Batch item done: item_id={item.item_id}, buildings={len(result['polygons'])}, gpt_count={result.get('gpt_count', 0)}, fallback_count={result['fallback_count']}")
        except Exception as e:
            item.status = ItemStatus.failed
            item.error = str(e)
            logger.error(f"Batch item failed: item_id={item.item_id}, error={e}")

        # Yield control between items
        await asyncio.sleep(0)

    all_failed = all(i.status == ItemStatus.failed for i in job.items)
    job.status = JobStatus.failed if all_failed else JobStatus.complete
    logger.info(f"Batch job complete: batch_id={batch_id}, status={job.status}")


@app.post("/api/batch/{batch_id}/run")
async def run_batch(batch_id: str, request: BatchRunRequest, background_tasks: BackgroundTasks):
    """Start sequential batch processing."""
    job = batch_jobs.get(batch_id)
    if not job:
        raise HTTPException(status_code=404, detail="Batch job not found.")
    if job.status != JobStatus.uploaded:
        raise HTTPException(status_code=400, detail=f"Job is already in state '{job.status}'.")

    available_models = model_manager.get_available_models()
    if request.model not in available_models:
        raise HTTPException(status_code=400, detail=f"Invalid model. Supported: {', '.join(available_models)}")

    job.model = request.model
    job.status = JobStatus.running
    background_tasks.add_task(_run_batch_job, batch_id)
    return {"status": "started"}


@app.get("/api/batch/{batch_id}/status", response_model=BatchStatusResponse)
async def get_batch_status(batch_id: str):
    """Poll batch job progress."""
    job = batch_jobs.get(batch_id)
    if not job:
        raise HTTPException(status_code=404, detail="Batch job not found.")

    counts = {s: 0 for s in ItemStatus}
    for item in job.items:
        counts[item.status] += 1

    return BatchStatusResponse(
        batch_id=batch_id,
        status=job.status,
        total=len(job.items),
        done=counts[ItemStatus.done],
        failed=counts[ItemStatus.failed],
        pending=counts[ItemStatus.pending],
        processing=counts[ItemStatus.processing],
        items=job.items,
    )


@app.post("/api/batch/{batch_id}/items/{item_id}/polygons")
async def update_item_polygons(batch_id: str, item_id: str, body: dict):
    """Save edited polygons for a single batch item."""
    job = batch_jobs.get(batch_id)
    if not job:
        raise HTTPException(status_code=404, detail="Batch job not found.")
    item = next((i for i in job.items if i.item_id == item_id), None)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found.")
    item.polygons = body.get("polygons", item.polygons)
    item.building_count = len(item.polygons)
    return {"status": "ok"}


@app.post("/api/batch/{batch_id}/items/{item_id}/retry")
async def retry_batch_item(batch_id: str, item_id: str, background_tasks: BackgroundTasks):
    """Retry a failed batch item using GPT-4o Vision boundary detection."""
    job = batch_jobs.get(batch_id)
    if not job:
        raise HTTPException(status_code=404, detail="Batch job not found.")
    item = next((i for i in job.items if i.item_id == item_id), None)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found.")
    if item.status != ItemStatus.failed:
        raise HTTPException(status_code=400, detail="Only failed items can be retried.")

    async def _retry():
        import cv2
        item.status = ItemStatus.processing
        item.error = ""
        try:
            api_key = os.getenv("OPENAI_API_KEY", "")
            extractor = GPTBoundaryExtractor(api_key=api_key)
            
            img_path = Path(item.image_path)
            image_array = image_processor.load_image(str(img_path))
            original_bgr = cv2.cvtColor(image_array, cv2.COLOR_RGB2BGR)
            
            mask = model_manager.segment(image_array, job.model)
            batch_mask_dir = BATCH_DIR / batch_id / "masks"
            mask_path = batch_mask_dir / f"{item.item_id}-mask.png"
            image_processor.save_mask(mask, str(mask_path))
            item.mask_path = str(mask_path)
            
            mask_gray = mask if len(mask.shape) == 2 else cv2.cvtColor(mask, cv2.COLOR_RGB2GRAY)
            model_obj = model_manager.get_model(job.model)
            if hasattr(model_obj, 'instance_segment'):
                instance_masks = model_obj.instance_segment(image_array)
            else:
                instance_masks = [mask_gray]
            
            result = await extractor.process_async(original_bgr, instance_masks)
            item.polygons = result["polygons"]
            item.building_count = len(result["polygons"])
            item.status = ItemStatus.done
        except Exception as e:
            item.status = ItemStatus.failed
            item.error = str(e)

    background_tasks.add_task(_retry)
    return {"status": "retrying"}


@app.get("/api/batch/{batch_id}/download")
async def download_batch(batch_id: str, format: str = "json"):
    """Download all processed results as a ZIP."""
    job = batch_jobs.get(batch_id)
    if not job:
        raise HTTPException(status_code=404, detail="Batch job not found.")

    done_items = [i for i in job.items if i.status == ItemStatus.done]
    if not done_items:
        raise HTTPException(status_code=400, detail="No successfully processed items to download.")

    if format not in ("json", "png", "jpeg"):
        raise HTTPException(status_code=400, detail="Format must be json, png, or jpeg.")

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for item in done_items:
            import cv2
            stem = Path(item.original_filename).stem

            if format == "json":
                # Normalise polygons to consistent dict format
                normalised = []
                for p in item.polygons:
                    if isinstance(p, list):
                        normalised.append({"points": p})
                    else:
                        normalised.append(p)
                data = {
                    "filename": item.original_filename,
                    "building_count": item.building_count,
                    "polygons": normalised,
                }
                import json
                zf.writestr(f"{stem}_output.json", json.dumps(data, indent=2))

            else:  # png or jpeg
                import cv2
                img_path = Path(item.image_path)
                image_array = image_processor.load_image(str(img_path))
                render = cv2.cvtColor(image_array, cv2.COLOR_RGB2BGR)

                # Draw polygons
                for building in item.polygons:
                    # Support both raw [[x,y],...] and dict formats
                    if isinstance(building, list):
                        pts = building
                    elif isinstance(building, dict):
                        pts = building.get("points") or building.get("coordinates") or []
                    else:
                        pts = []
                    if pts:
                        pts_arr = np.array(pts, dtype=np.int32).reshape((-1, 1, 2))
                        cv2.polylines(render, [pts_arr], isClosed=True, color=(0, 255, 0), thickness=2)

                ext = ".jpg" if format == "jpeg" else ".png"
                encode_ext = ".jpg" if format == "jpeg" else ".png"
                _, encoded = cv2.imencode(encode_ext, render)
                zf.writestr(f"{stem}_output{ext}", encoded.tobytes())

    buf.seek(0)
    return StreamingResponse(
        buf,
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename=batch_{batch_id}_results.zip"},
    )

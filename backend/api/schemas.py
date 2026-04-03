"""Pydantic request/response schemas for the API."""

from enum import Enum
from pydantic import BaseModel


# ── Error ────────────────────────────────────────────────────────────────────

class ErrorResponse(BaseModel):
    detail: str
    timestamp: str
    path: str = ""


# ── Segmentation ─────────────────────────────────────────────────────────────

class UploadResponse(BaseModel):
    image_id: str
    image_url: str
    width: int
    height: int


class SegmentRequest(BaseModel):
    image_id: str
    model: str


class SegmentResponse(BaseModel):
    mask_url: str
    mask_base64: str
    processing_time: float
    model_used: str


class ModelInfo(BaseModel):
    name: str
    display_name: str
    description: str


class ModelsResponse(BaseModel):
    models: list[ModelInfo]


# ── Boundaries ───────────────────────────────────────────────────────────────

class BoundaryRequest(BaseModel):
    image_id: str
    model: str


class BoundaryResponse(BaseModel):
    buildings: list
    total_buildings: int
    processing_time: float


class GPTBoundaryRequest(BaseModel):
    image_id: str
    model: str  # yolov8m-custom | maskrcnn-custom


class GPTBoundaryResponse(BaseModel):
    gpt_overlay_b64: str
    opencv_overlay_b64: str
    building_count: int
    polygons: list
    processing_time_s: float
    fallback_count: int
    gpt_count: int = 0
    fallback_reasons: dict = {}
    image_url: str = ""


# ── Batch ────────────────────────────────────────────────────────────────────

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

# Models package initialization

from .segmentation_model import SegmentationModel

# Lazy import for adapters to avoid requiring heavy dependencies at import time
def _get_sam2_adapter():
    from .sam2_adapter import SAM2Adapter
    return SAM2Adapter

def _get_yolov8_adapter():
    from .yolov8_adapter import YOLOv8Adapter
    return YOLOv8Adapter

def _get_unet_adapter():
    from .unet_adapter import UNetAdapter
    return UNetAdapter

def _get_segmentation_model_manager():
    from .segmentation_model_manager import SegmentationModelManager
    return SegmentationModelManager

__all__ = ['SegmentationModel', 'SAM2Adapter', 'YOLOv8Adapter', 'UNetAdapter', 'SegmentationModelManager']

# Make adapters available but only import when accessed
def __getattr__(name):
    if name == 'SAM2Adapter':
        return _get_sam2_adapter()
    elif name == 'YOLOv8Adapter':
        return _get_yolov8_adapter()
    elif name == 'UNetAdapter':
        return _get_unet_adapter()
    elif name == 'SegmentationModelManager':
        return _get_segmentation_model_manager()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

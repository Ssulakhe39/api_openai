"""
Segmentation Model Manager for managing and routing segmentation requests.

This module provides a centralized manager for loading and executing different
segmentation models (SAM2, YOLOv8, U-Net). It implements lazy loading to only
initialize models when first requested, improving startup time and memory usage.
"""

from typing import Dict, Optional
import numpy as np
import importlib.util

from .segmentation_model import SegmentationModel

# Check if SAM2 is available
SAM2_AVAILABLE = importlib.util.find_spec("sam2") is not None

if SAM2_AVAILABLE:
    try:
        from .sam2_adapter import SAM2Adapter
    except ImportError:
        SAM2_AVAILABLE = False
        SAM2Adapter = None
else:
    SAM2Adapter = None

from .yolov8_adapter import YOLOv8Adapter
from .unet_adapter import UNetAdapter
from .maskrcnn_adapter import MaskRCNNAdapter


class SegmentationModelManager:
    """
    Manager for segmentation models with lazy loading support.
    
    This class manages multiple segmentation model instances and provides
    a unified interface for loading and executing segmentation. Models are
    loaded lazily - they are only initialized when first requested, which
    improves startup time and reduces memory usage.
    
    Attributes:
        models: Dictionary mapping model names to loaded model instances
        model_configs: Dictionary mapping model names to their configuration
    """
    
    def __init__(self):
        """Initialize the model manager with empty model registry."""
        self.models: Dict[str, SegmentationModel] = {}
        self.model_configs: Dict[str, dict] = {}
        
        # Add SAM2 only if available
        if SAM2_AVAILABLE:
            self.model_configs['sam2'] = {
                'class': SAM2Adapter,
                'checkpoint_path': 'checkpoints/sam2_hiera_large.pt',
                'model_cfg': 'sam2_hiera_l.yaml'
            }
        
        # Add custom YOLOv8m segmentation model trained on building dataset
        self.model_configs['yolov8m-custom'] = {
            'class': YOLOv8Adapter,
            'model_path': r'D:\model weights\best_fixed.pt'  # Fixed/rebuilt model
        }
        
        # Add custom Mask R-CNN segmentation model trained on building dataset
        self.model_configs['maskrcnn-custom'] = {
            'class': MaskRCNNAdapter,
            'model_path': r'D:\model weights\maskrcnn_building_best.pth',  # Custom trained model
            'num_classes': 2  # Background + building
        }
    
    def load_model(self, model_name: str) -> None:
        """
        Load specified model into memory.
        
        This method initializes the specified model and loads its weights.
        If the model is already loaded, this method does nothing (idempotent).
        
        Args:
            model_name: Name of the model to load ('sam2', 'yolov8', or 'unet')
        
        Raises:
            ValueError: If model_name is not supported
            Exception: If model loading fails
        """
        # Check if model is already loaded
        if model_name in self.models:
            return
        
        # Validate model name
        if model_name not in self.model_configs:
            supported = ', '.join(self.model_configs.keys())
            raise ValueError(
                f"Unsupported model: '{model_name}'. "
                f"Supported models: {supported}"
            )
        
        # Get model configuration
        config = self.model_configs[model_name]
        model_class = config['class']
        
        # Create model instance based on type
        if model_name == 'sam2':
            model = model_class(
                checkpoint_path=config['checkpoint_path'],
                model_cfg=config['model_cfg']
            )
        elif model_name in ['yolov8', 'yolov8m-custom']:
            model = model_class(
                model_path=config['model_path']
            )
        elif model_name == 'maskrcnn-custom':
            model = model_class(
                model_path=config['model_path'],
                num_classes=config.get('num_classes', 2)
            )
        elif model_name == 'unet':
            model = model_class(
                model_path=config['model_path'],
                framework=config['framework']
            )
        elif model_name == 'unet-aerial':
            model = model_class(
                model_path=config['model_path']
            )
        else:
            # Generic fallback for new models
            model = model_class(**{k: v for k, v in config.items() if k != 'class'})
        
        # Load model weights
        model.load()
        
        # Store loaded model
        self.models[model_name] = model
    
    def get_model(self, model_name: str) -> SegmentationModel:
        """
        Get loaded model instance.
        
        This method returns the specified model instance. If the model is not
        yet loaded, it will be loaded automatically (lazy loading).
        
        Args:
            model_name: Name of the model to retrieve ('sam2', 'yolov8', or 'unet')
        
        Returns:
            Loaded model instance implementing SegmentationModel interface
        
        Raises:
            ValueError: If model_name is not supported
            Exception: If model loading fails
        """
        # Load model if not already loaded (lazy loading)
        if model_name not in self.models:
            self.load_model(model_name)
        
        return self.models[model_name]
    
    def segment(self, image: np.ndarray, model_name: str) -> np.ndarray:
        """
        Run segmentation using specified model.
        
        This method routes the segmentation request to the appropriate model.
        The model is loaded automatically if not already in memory (lazy loading).
        
        Args:
            image: Input image as numpy array with shape (H, W, C) and dtype uint8
            model_name: Name of the model to use ('sam2', 'yolov8', or 'unet')
        
        Returns:
            Binary segmentation mask as numpy array with shape (H, W),
            dtype uint8, and values in {0, 255}
        
        Raises:
            ValueError: If model_name is not supported
            Exception: If segmentation fails
        """
        # Get model (loads if necessary)
        model = self.get_model(model_name)
        
        # Run segmentation
        mask = model.segment(image)
        
        return mask
    
    def is_model_loaded(self, model_name: str) -> bool:
        """
        Check if a model is currently loaded in memory.
        
        Args:
            model_name: Name of the model to check
        
        Returns:
            True if model is loaded, False otherwise
        """
        return model_name in self.models
    
    def unload_model(self, model_name: str) -> None:
        """
        Unload a model from memory.
        
        This method removes the model from the registry, allowing it to be
        garbage collected. Useful for freeing memory when a model is no longer needed.
        
        Args:
            model_name: Name of the model to unload
        """
        if model_name in self.models:
            del self.models[model_name]
    
    def get_available_models(self) -> list:
        """
        Get list of available model names.
        
        Returns:
            List of supported model names
        """
        return list(self.model_configs.keys())

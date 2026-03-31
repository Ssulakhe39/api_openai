"""
Unit tests for SegmentationModelManager.

This module tests the model manager's ability to load, manage, and route
segmentation requests to different models with lazy loading support.
"""

import pytest
import numpy as np
import sys
from unittest.mock import Mock, patch, MagicMock

# Mock torch and model-specific modules before importing
mock_torch = MagicMock()
mock_torch.nn = MagicMock()
mock_torch.cuda = MagicMock()
mock_torch.cuda.is_available = MagicMock(return_value=False)
sys.modules['torch'] = mock_torch
sys.modules['torch.nn'] = mock_torch.nn
sys.modules['sam2'] = Mock()
sys.modules['sam2.build_sam'] = Mock()
sys.modules['sam2.automatic_mask_generator'] = Mock()
sys.modules['ultralytics'] = Mock()

from backend.models.segmentation_model_manager import SegmentationModelManager
from backend.models.segmentation_model import SegmentationModel


class TestSegmentationModelManager:
    """Test suite for SegmentationModelManager."""
    
    def test_initialization(self):
        """Test that manager initializes with empty model registry."""
        manager = SegmentationModelManager()
        
        assert isinstance(manager.models, dict)
        assert len(manager.models) == 0
        assert 'sam2' in manager.model_configs
        assert 'yolov8' in manager.model_configs
        assert 'unet' in manager.model_configs
    
    def test_get_available_models(self):
        """Test getting list of available models."""
        manager = SegmentationModelManager()
        
        available = manager.get_available_models()
        
        assert isinstance(available, list)
        assert 'sam2' in available
        assert 'yolov8' in available
        assert 'unet' in available
        assert len(available) == 3
    
    def test_is_model_loaded_false(self):
        """Test checking if model is loaded when it's not."""
        manager = SegmentationModelManager()
        
        assert manager.is_model_loaded('sam2') is False
        assert manager.is_model_loaded('yolov8') is False
        assert manager.is_model_loaded('unet') is False
    
    @patch('backend.models.segmentation_model_manager.SAM2Adapter')
    def test_load_model_sam2(self, mock_sam2_class):
        """Test loading SAM2 model."""
        # Setup mock
        mock_model = Mock(spec=SegmentationModel)
        mock_sam2_class.return_value = mock_model
        
        manager = SegmentationModelManager()
        manager.load_model('sam2')
        
        # Verify model was created with correct parameters
        mock_sam2_class.assert_called_once_with(
            checkpoint_path='models/sam2_hiera_l.pt',
            model_cfg='sam2_hiera_l.yaml'
        )
        
        # Verify load was called
        mock_model.load.assert_called_once()
        
        # Verify model is stored
        assert 'sam2' in manager.models
        assert manager.models['sam2'] == mock_model
        assert manager.is_model_loaded('sam2') is True
    
    @patch('backend.models.segmentation_model_manager.YOLOv8Adapter')
    def test_load_model_yolov8(self, mock_yolo_class):
        """Test loading YOLOv8 model."""
        # Setup mock
        mock_model = Mock(spec=SegmentationModel)
        mock_yolo_class.return_value = mock_model
        
        manager = SegmentationModelManager()
        manager.load_model('yolov8')
        
        # Verify model was created with correct parameters
        mock_yolo_class.assert_called_once_with(
            model_path='models/yolov8n-seg.pt'
        )
        
        # Verify load was called
        mock_model.load.assert_called_once()
        
        # Verify model is stored
        assert 'yolov8' in manager.models
        assert manager.models['yolov8'] == mock_model
    
    @patch('backend.models.segmentation_model_manager.UNetAdapter')
    def test_load_model_unet(self, mock_unet_class):
        """Test loading U-Net model."""
        # Setup mock
        mock_model = Mock(spec=SegmentationModel)
        mock_unet_class.return_value = mock_model
        
        manager = SegmentationModelManager()
        manager.load_model('unet')
        
        # Verify model was created with correct parameters
        mock_unet_class.assert_called_once_with(
            model_path='models/unet_buildings.pt',
            framework='pytorch'
        )
        
        # Verify load was called
        mock_model.load.assert_called_once()
        
        # Verify model is stored
        assert 'unet' in manager.models
        assert manager.models['unet'] == mock_model
    
    def test_load_model_invalid_name(self):
        """Test loading model with invalid name raises ValueError."""
        manager = SegmentationModelManager()
        
        with pytest.raises(ValueError) as exc_info:
            manager.load_model('invalid_model')
        
        assert 'Unsupported model' in str(exc_info.value)
        assert 'invalid_model' in str(exc_info.value)
    
    @patch('backend.models.segmentation_model_manager.SAM2Adapter')
    def test_load_model_idempotent(self, mock_sam2_class):
        """Test that loading same model twice doesn't reload it."""
        # Setup mock
        mock_model = Mock(spec=SegmentationModel)
        mock_sam2_class.return_value = mock_model
        
        manager = SegmentationModelManager()
        
        # Load model twice
        manager.load_model('sam2')
        manager.load_model('sam2')
        
        # Verify model was only created once
        mock_sam2_class.assert_called_once()
        mock_model.load.assert_called_once()
    
    @patch('backend.models.segmentation_model_manager.SAM2Adapter')
    def test_get_model_already_loaded(self, mock_sam2_class):
        """Test getting model that's already loaded."""
        # Setup mock
        mock_model = Mock(spec=SegmentationModel)
        mock_sam2_class.return_value = mock_model
        
        manager = SegmentationModelManager()
        manager.load_model('sam2')
        
        # Get model
        retrieved_model = manager.get_model('sam2')
        
        # Verify same model instance is returned
        assert retrieved_model == mock_model
        
        # Verify load was only called once (not again during get)
        mock_model.load.assert_called_once()
    
    @patch('backend.models.segmentation_model_manager.YOLOv8Adapter')
    def test_get_model_lazy_loading(self, mock_yolo_class):
        """Test that get_model loads model if not already loaded (lazy loading)."""
        # Setup mock
        mock_model = Mock(spec=SegmentationModel)
        mock_yolo_class.return_value = mock_model
        
        manager = SegmentationModelManager()
        
        # Get model without loading first
        retrieved_model = manager.get_model('yolov8')
        
        # Verify model was loaded automatically
        mock_yolo_class.assert_called_once()
        mock_model.load.assert_called_once()
        assert retrieved_model == mock_model
        assert manager.is_model_loaded('yolov8') is True
    
    def test_get_model_invalid_name(self):
        """Test getting model with invalid name raises ValueError."""
        manager = SegmentationModelManager()
        
        with pytest.raises(ValueError) as exc_info:
            manager.get_model('nonexistent')
        
        assert 'Unsupported model' in str(exc_info.value)
    
    @patch('backend.models.segmentation_model_manager.UNetAdapter')
    def test_segment(self, mock_unet_class):
        """Test segmentation routing to correct model."""
        # Setup mock
        mock_model = Mock(spec=SegmentationModel)
        expected_mask = np.zeros((100, 100), dtype=np.uint8)
        mock_model.segment.return_value = expected_mask
        mock_model.load.return_value = None
        mock_unet_class.return_value = mock_model
        
        manager = SegmentationModelManager()
        
        # Create test image
        test_image = np.random.randint(0, 256, (100, 100, 3), dtype=np.uint8)
        
        # Run segmentation
        result_mask = manager.segment(test_image, 'unet')
        
        # Verify model was instantiated with correct parameters
        mock_unet_class.assert_called_once_with(
            model_path='models/unet_buildings.pt',
            framework='pytorch'
        )
        mock_model.load.assert_called_once()
        
        # Verify segment was called with correct image
        mock_model.segment.assert_called_once()
        call_args = mock_model.segment.call_args[0]
        np.testing.assert_array_equal(call_args[0], test_image)
        
        # Verify correct mask is returned
        np.testing.assert_array_equal(result_mask, expected_mask)
    
    @patch('backend.models.segmentation_model_manager.SAM2Adapter')
    @patch('backend.models.segmentation_model_manager.YOLOv8Adapter')
    def test_segment_multiple_models(self, mock_yolo_class, mock_sam2_class):
        """Test segmentation with different models maintains independence."""
        # Setup mocks
        mock_sam2 = Mock(spec=SegmentationModel)
        mock_yolo = Mock(spec=SegmentationModel)
        
        sam2_mask = np.ones((50, 50), dtype=np.uint8) * 255
        yolo_mask = np.zeros((50, 50), dtype=np.uint8)
        
        mock_sam2.segment.return_value = sam2_mask
        mock_yolo.segment.return_value = yolo_mask
        mock_sam2.load.return_value = None
        mock_yolo.load.return_value = None
        
        mock_sam2_class.return_value = mock_sam2
        mock_yolo_class.return_value = mock_yolo
        
        manager = SegmentationModelManager()
        
        # Create test image
        test_image = np.random.randint(0, 256, (50, 50, 3), dtype=np.uint8)
        
        # Run segmentation with both models
        result1 = manager.segment(test_image, 'sam2')
        result2 = manager.segment(test_image, 'yolov8')
        
        # Verify both models were loaded
        assert manager.is_model_loaded('sam2')
        assert manager.is_model_loaded('yolov8')
        
        # Verify correct masks are returned
        np.testing.assert_array_equal(result1, sam2_mask)
        np.testing.assert_array_equal(result2, yolo_mask)
        
        # Verify each model's segment was called once
        mock_sam2.segment.assert_called_once()
        mock_yolo.segment.assert_called_once()
    
    @patch('backend.models.segmentation_model_manager.SAM2Adapter')
    def test_unload_model(self, mock_sam2_class):
        """Test unloading a model from memory."""
        # Setup mock
        mock_model = Mock(spec=SegmentationModel)
        mock_sam2_class.return_value = mock_model
        
        manager = SegmentationModelManager()
        manager.load_model('sam2')
        
        assert manager.is_model_loaded('sam2')
        
        # Unload model
        manager.unload_model('sam2')
        
        assert manager.is_model_loaded('sam2') is False
        assert 'sam2' not in manager.models
    
    def test_unload_model_not_loaded(self):
        """Test unloading model that's not loaded doesn't raise error."""
        manager = SegmentationModelManager()
        
        # Should not raise any exception
        manager.unload_model('sam2')
        
        assert manager.is_model_loaded('sam2') is False
    
    @patch('backend.models.segmentation_model_manager.SAM2Adapter')
    def test_model_loading_failure(self, mock_sam2_class):
        """Test that model loading failures are propagated."""
        # Setup mock to raise exception during load
        mock_model = Mock(spec=SegmentationModel)
        mock_model.load.side_effect = Exception("Model file not found")
        mock_sam2_class.return_value = mock_model
        
        manager = SegmentationModelManager()
        
        with pytest.raises(Exception) as exc_info:
            manager.load_model('sam2')
        
        assert "Model file not found" in str(exc_info.value)
        
        # Verify model is not in registry after failed load
        assert manager.is_model_loaded('sam2') is False
    
    @patch('backend.models.segmentation_model_manager.YOLOv8Adapter')
    def test_segment_with_model_error(self, mock_yolo_class):
        """Test that segmentation errors are propagated."""
        # Setup mock to raise exception during segment
        mock_model = Mock(spec=SegmentationModel)
        mock_model.load.return_value = None
        mock_model.segment.side_effect = Exception("Segmentation failed")
        mock_yolo_class.return_value = mock_model
        
        manager = SegmentationModelManager()
        test_image = np.random.randint(0, 256, (100, 100, 3), dtype=np.uint8)
        
        with pytest.raises(Exception) as exc_info:
            manager.segment(test_image, 'yolov8')
        
        assert "Segmentation failed" in str(exc_info.value)

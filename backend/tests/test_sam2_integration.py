"""
Integration test for SAM2Adapter to verify it meets all task requirements.

Task 3.2 Requirements:
- Load SAM2 model using segment-anything-2 library ✓
- Implement preprocessing (RGB conversion, normalization) ✓
- Implement prediction using automatic mask generation ✓
- Implement postprocessing to combine masks into binary output ✓
- Requirements: 2.1, 3.1, 3.4
"""

import pytest
import numpy as np
import sys
from unittest.mock import Mock, patch

# Mock torch and SAM2 modules
sys.modules['torch'] = Mock()
sys.modules['sam2'] = Mock()
sys.modules['sam2.build_sam'] = Mock()
sys.modules['sam2.automatic_mask_generator'] = Mock()

from backend.models.sam2_adapter import SAM2Adapter
from backend.models.segmentation_model import SegmentationModel


class TestSAM2AdapterRequirements:
    """Test that SAM2Adapter meets all specified requirements."""
    
    def test_implements_segmentation_model_interface(self):
        """Requirement 2.1: SAM2Adapter implements SegmentationModel interface."""
        adapter = SAM2Adapter(
            checkpoint_path="/path/to/checkpoint.pth",
            model_cfg="sam2_hiera_l.yaml"
        )
        
        # Verify it's a subclass of SegmentationModel
        assert isinstance(adapter, SegmentationModel)
        
        # Verify all required methods are implemented
        assert hasattr(adapter, 'load')
        assert hasattr(adapter, 'preprocess')
        assert hasattr(adapter, 'predict')
        assert hasattr(adapter, 'postprocess')
        assert hasattr(adapter, 'segment')
        
        # Verify methods are callable
        assert callable(adapter.load)
        assert callable(adapter.preprocess)
        assert callable(adapter.predict)
        assert callable(adapter.postprocess)
        assert callable(adapter.segment)
    
    @patch('backend.models.sam2_adapter.build_sam2')
    @patch('backend.models.sam2_adapter.SAM2AutomaticMaskGenerator')
    def test_loads_sam2_model(self, mock_generator, mock_build):
        """Task requirement: Load SAM2 model using segment-anything-2 library."""
        mock_model = Mock()
        mock_build.return_value = mock_model
        mock_generator.return_value = Mock()
        
        adapter = SAM2Adapter(
            checkpoint_path="/path/to/checkpoint.pth",
            model_cfg="sam2_hiera_l.yaml"
        )
        adapter.load()
        
        # Verify build_sam2 was called (from segment-anything-2 library)
        mock_build.assert_called_once()
        
        # Verify SAM2AutomaticMaskGenerator was created
        mock_generator.assert_called_once()
        assert mock_generator.call_args.kwargs['model'] == mock_model
    
    def test_preprocessing_rgb_conversion(self):
        """Task requirement: Implement preprocessing (RGB conversion, normalization)."""
        adapter = SAM2Adapter(
            checkpoint_path="/path/to/checkpoint.pth",
            model_cfg="sam2_hiera_l.yaml"
        )
        
        # Test RGB conversion (ensures 3 channels)
        image_rgb = np.random.randint(0, 256, (100, 100, 3), dtype=np.uint8)
        preprocessed = adapter.preprocess(image_rgb)
        
        assert preprocessed.shape[2] == 3, "Should maintain RGB format"
        assert preprocessed.dtype == np.uint8, "Should be uint8 format"
        
        # Test that non-RGB images are rejected
        image_rgba = np.random.randint(0, 256, (100, 100, 4), dtype=np.uint8)
        with pytest.raises(ValueError, match="Expected 3-channel RGB image"):
            adapter.preprocess(image_rgba)
    
    @patch('backend.models.sam2_adapter.build_sam2')
    @patch('backend.models.sam2_adapter.SAM2AutomaticMaskGenerator')
    def test_prediction_uses_automatic_mask_generation(self, mock_generator, mock_build):
        """Task requirement: Implement prediction using automatic mask generation."""
        # Setup mocks
        mock_predictor = Mock()
        mock_masks = [
            {'segmentation': np.ones((100, 100), dtype=bool), 'area': 10000}
        ]
        mock_predictor.generate.return_value = mock_masks
        mock_generator.return_value = mock_predictor
        mock_build.return_value = Mock()
        
        adapter = SAM2Adapter(
            checkpoint_path="/path/to/checkpoint.pth",
            model_cfg="sam2_hiera_l.yaml"
        )
        adapter.load()
        
        image = np.random.randint(0, 256, (100, 100, 3), dtype=np.uint8)
        masks = adapter.predict(image)
        
        # Verify automatic mask generation was used
        mock_predictor.generate.assert_called_once_with(image)
        assert masks == mock_masks
    
    def test_postprocessing_combines_masks_to_binary(self):
        """Task requirement: Implement postprocessing to combine masks into binary output."""
        adapter = SAM2Adapter(
            checkpoint_path="/path/to/checkpoint.pth",
            model_cfg="sam2_hiera_l.yaml"
        )
        
        # Create multiple masks
        mask1 = np.zeros((100, 100), dtype=bool)
        mask1[10:30, 10:30] = True
        
        mask2 = np.zeros((100, 100), dtype=bool)
        mask2[70:90, 70:90] = True
        
        raw_output = [
            {'segmentation': mask1, 'area': 400},
            {'segmentation': mask2, 'area': 400}
        ]
        
        result = adapter.postprocess(raw_output)
        
        # Verify masks are combined
        assert result.shape == (100, 100), "Should maintain image dimensions"
        assert result.dtype == np.uint8, "Should be uint8"
        
        # Verify binary output (0 or 255)
        unique_values = np.unique(result)
        assert all(v in [0, 255] for v in unique_values), "Should be binary (0 or 255)"
        
        # Verify both mask regions are present
        assert np.all(result[10:30, 10:30] == 255), "First mask region should be 255"
        assert np.all(result[70:90, 70:90] == 255), "Second mask region should be 255"
        assert result[0, 0] == 0, "Background should be 0"
    
    @patch('backend.models.sam2_adapter.build_sam2')
    @patch('backend.models.sam2_adapter.SAM2AutomaticMaskGenerator')
    def test_requirement_3_1_segmentation_execution(self, mock_generator, mock_build):
        """Requirement 3.1: System shall process image using selected segmentation model."""
        # Setup mocks
        mock_predictor = Mock()
        mask = np.zeros((256, 256), dtype=bool)
        mask[50:150, 50:150] = True
        mock_predictor.generate.return_value = [
            {'segmentation': mask, 'area': 10000}
        ]
        mock_generator.return_value = mock_predictor
        mock_build.return_value = Mock()
        
        adapter = SAM2Adapter(
            checkpoint_path="/path/to/checkpoint.pth",
            model_cfg="sam2_hiera_l.yaml"
        )
        adapter.load()
        
        # Process image
        image = np.random.randint(0, 256, (256, 256, 3), dtype=np.uint8)
        result = adapter.segment(image)
        
        # Verify processing occurred
        assert result is not None
        assert isinstance(result, np.ndarray)
    
    @patch('backend.models.sam2_adapter.build_sam2')
    @patch('backend.models.sam2_adapter.SAM2AutomaticMaskGenerator')
    def test_requirement_3_4_binary_mask_generation(self, mock_generator, mock_build):
        """Requirement 3.4: System shall generate a binary segmentation mask."""
        # Setup mocks
        mock_predictor = Mock()
        mask = np.zeros((256, 256), dtype=bool)
        mask[50:150, 50:150] = True
        mock_predictor.generate.return_value = [
            {'segmentation': mask, 'area': 10000}
        ]
        mock_generator.return_value = mock_predictor
        mock_build.return_value = Mock()
        
        adapter = SAM2Adapter(
            checkpoint_path="/path/to/checkpoint.pth",
            model_cfg="sam2_hiera_l.yaml"
        )
        adapter.load()
        
        image = np.random.randint(0, 256, (256, 256, 3), dtype=np.uint8)
        mask = adapter.segment(image)
        
        # Verify binary mask
        assert mask.dtype == np.uint8, "Mask should be uint8"
        unique_values = np.unique(mask)
        assert set(unique_values).issubset({0, 255}), "Mask should only contain 0 or 255"
        assert len(unique_values) <= 2, "Mask should be binary"
    
    @patch('backend.models.sam2_adapter.build_sam2')
    @patch('backend.models.sam2_adapter.SAM2AutomaticMaskGenerator')
    def test_complete_pipeline_integration(self, mock_generator, mock_build):
        """Test complete pipeline: load → preprocess → predict → postprocess."""
        # Setup mocks
        mock_predictor = Mock()
        mask = np.zeros((512, 512), dtype=bool)
        mask[100:400, 100:400] = True  # Large building in center
        mock_predictor.generate.return_value = [
            {'segmentation': mask, 'area': 90000}
        ]
        mock_generator.return_value = mock_predictor
        mock_build.return_value = Mock()
        
        # Create adapter
        adapter = SAM2Adapter(
            checkpoint_path="/path/to/checkpoint.pth",
            model_cfg="sam2_hiera_l.yaml"
        )
        
        # Load model
        adapter.load()
        assert adapter.predictor is not None
        
        # Create test image
        image = np.random.randint(0, 256, (512, 512, 3), dtype=np.uint8)
        
        # Run complete pipeline
        result = adapter.segment(image)
        
        # Verify output meets all requirements
        assert result.shape == (512, 512), "Output should match input dimensions"
        assert result.dtype == np.uint8, "Output should be uint8"
        assert set(np.unique(result)).issubset({0, 255}), "Output should be binary"
        assert np.sum(result == 255) == 90000, "Building pixels should match mask area"
        assert np.all(result[100:400, 100:400] == 255), "Building region should be marked"
        assert result[0, 0] == 0, "Background should be 0"

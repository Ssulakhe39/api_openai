"""
Unit tests for SAM2Adapter.

Tests verify that:
1. SAM2Adapter correctly implements the SegmentationModel interface
2. Preprocessing converts images to the correct format for SAM2
3. Postprocessing combines masks correctly into binary output
4. Error handling works correctly for edge cases
"""

import pytest
import numpy as np
import sys
from unittest.mock import Mock, patch, MagicMock

# Mock torch and SAM2 modules before importing SAM2Adapter
sys.modules['torch'] = Mock()
sys.modules['sam2'] = Mock()
sys.modules['sam2.build_sam'] = Mock()
sys.modules['sam2.automatic_mask_generator'] = Mock()

from backend.models.sam2_adapter import SAM2Adapter


class TestSAM2AdapterInitialization:
    """Test SAM2Adapter initialization and loading."""
    
    def test_initialization(self):
        """SAM2Adapter should initialize with checkpoint and config paths."""
        adapter = SAM2Adapter(
            checkpoint_path="/path/to/checkpoint.pth",
            model_cfg="sam2_hiera_l.yaml"
        )
        
        assert adapter.checkpoint_path == "/path/to/checkpoint.pth"
        assert adapter.model_cfg == "sam2_hiera_l.yaml"
        assert adapter.predictor is None  # Not loaded yet
    
    @patch('backend.models.sam2_adapter.build_sam2')
    @patch('backend.models.sam2_adapter.SAM2AutomaticMaskGenerator')
    def test_load_success(self, mock_generator, mock_build):
        """load() should successfully initialize SAM2 model and mask generator."""
        # Setup mocks
        mock_model = Mock()
        mock_build.return_value = mock_model
        mock_predictor = Mock()
        mock_generator.return_value = mock_predictor
        
        adapter = SAM2Adapter(
            checkpoint_path="/path/to/checkpoint.pth",
            model_cfg="sam2_hiera_l.yaml"
        )
        adapter.load()
        
        # Verify build_sam2 was called with correct arguments
        mock_build.assert_called_once()
        call_kwargs = mock_build.call_args.kwargs
        assert call_kwargs['config_file'] == "sam2_hiera_l.yaml"
        assert call_kwargs['ckpt_path'] == "/path/to/checkpoint.pth"
        assert call_kwargs['device'] in ['cuda', 'cpu']
        
        # Verify mask generator was created
        mock_generator.assert_called_once()
        assert mock_generator.call_args.kwargs['model'] == mock_model
        
        # Verify predictor is set
        assert adapter.predictor == mock_predictor
    
    @patch('backend.models.sam2_adapter.build_sam2')
    def test_load_failure(self, mock_build):
        """load() should raise exception if model loading fails."""
        mock_build.side_effect = Exception("Model file not found")
        
        adapter = SAM2Adapter(
            checkpoint_path="/invalid/path.pth",
            model_cfg="sam2_hiera_l.yaml"
        )
        
        with pytest.raises(Exception, match="Failed to load SAM2 model"):
            adapter.load()


class TestSAM2AdapterPreprocessing:
    """Test SAM2Adapter preprocessing."""
    
    def test_preprocess_valid_rgb_image(self):
        """preprocess() should accept valid RGB uint8 images."""
        adapter = SAM2Adapter(
            checkpoint_path="/path/to/checkpoint.pth",
            model_cfg="sam2_hiera_l.yaml"
        )
        
        image = np.random.randint(0, 256, (100, 100, 3), dtype=np.uint8)
        preprocessed = adapter.preprocess(image)
        
        assert preprocessed.shape == (100, 100, 3)
        assert preprocessed.dtype == np.uint8
        assert np.array_equal(preprocessed, image)
    
    def test_preprocess_converts_dtype(self):
        """preprocess() should convert non-uint8 images to uint8."""
        adapter = SAM2Adapter(
            checkpoint_path="/path/to/checkpoint.pth",
            model_cfg="sam2_hiera_l.yaml"
        )
        
        # Create float32 image
        image = np.random.rand(100, 100, 3).astype(np.float32) * 255
        preprocessed = adapter.preprocess(image)
        
        assert preprocessed.dtype == np.uint8
        assert preprocessed.shape == (100, 100, 3)
    
    def test_preprocess_rejects_wrong_channels(self):
        """preprocess() should reject images without 3 channels."""
        adapter = SAM2Adapter(
            checkpoint_path="/path/to/checkpoint.pth",
            model_cfg="sam2_hiera_l.yaml"
        )
        
        # Test with 4 channels (RGBA)
        image_rgba = np.random.randint(0, 256, (100, 100, 4), dtype=np.uint8)
        with pytest.raises(ValueError, match="Expected 3-channel RGB image"):
            adapter.preprocess(image_rgba)
        
        # Test with 1 channel (grayscale)
        image_gray = np.random.randint(0, 256, (100, 100, 1), dtype=np.uint8)
        with pytest.raises(ValueError, match="Expected 3-channel RGB image"):
            adapter.preprocess(image_gray)
    
    def test_preprocess_various_sizes(self):
        """preprocess() should handle various image sizes."""
        adapter = SAM2Adapter(
            checkpoint_path="/path/to/checkpoint.pth",
            model_cfg="sam2_hiera_l.yaml"
        )
        
        test_sizes = [(64, 64, 3), (128, 256, 3), (512, 512, 3), (1024, 768, 3)]
        
        for size in test_sizes:
            image = np.random.randint(0, 256, size, dtype=np.uint8)
            preprocessed = adapter.preprocess(image)
            
            assert preprocessed.shape == size
            assert preprocessed.dtype == np.uint8


class TestSAM2AdapterPrediction:
    """Test SAM2Adapter prediction."""
    
    @patch('backend.models.sam2_adapter.build_sam2')
    @patch('backend.models.sam2_adapter.SAM2AutomaticMaskGenerator')
    def test_predict_success(self, mock_generator, mock_build):
        """predict() should call SAM2 mask generator and return masks."""
        # Setup mocks
        mock_predictor = Mock()
        mock_masks = [
            {'segmentation': np.ones((100, 100), dtype=bool), 'area': 10000},
            {'segmentation': np.zeros((100, 100), dtype=bool), 'area': 0}
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
        
        # Verify generate was called
        mock_predictor.generate.assert_called_once_with(image)
        
        # Verify masks are returned
        assert masks == mock_masks
        assert len(masks) == 2
    
    def test_predict_without_loading(self):
        """predict() should raise exception if model not loaded."""
        adapter = SAM2Adapter(
            checkpoint_path="/path/to/checkpoint.pth",
            model_cfg="sam2_hiera_l.yaml"
        )
        
        image = np.random.randint(0, 256, (100, 100, 3), dtype=np.uint8)
        
        with pytest.raises(Exception, match="Model not loaded"):
            adapter.predict(image)
    
    @patch('backend.models.sam2_adapter.build_sam2')
    @patch('backend.models.sam2_adapter.SAM2AutomaticMaskGenerator')
    def test_predict_failure(self, mock_generator, mock_build):
        """predict() should raise exception if SAM2 prediction fails."""
        # Setup mocks
        mock_predictor = Mock()
        mock_predictor.generate.side_effect = RuntimeError("CUDA out of memory")
        mock_generator.return_value = mock_predictor
        mock_build.return_value = Mock()
        
        adapter = SAM2Adapter(
            checkpoint_path="/path/to/checkpoint.pth",
            model_cfg="sam2_hiera_l.yaml"
        )
        adapter.load()
        
        image = np.random.randint(0, 256, (100, 100, 3), dtype=np.uint8)
        
        with pytest.raises(Exception, match="SAM2 prediction failed"):
            adapter.predict(image)


class TestSAM2AdapterPostprocessing:
    """Test SAM2Adapter postprocessing."""
    
    def test_postprocess_single_mask(self):
        """postprocess() should convert single mask to binary format."""
        adapter = SAM2Adapter(
            checkpoint_path="/path/to/checkpoint.pth",
            model_cfg="sam2_hiera_l.yaml"
        )
        
        # Create mock SAM2 output with one mask
        mask = np.zeros((100, 100), dtype=bool)
        mask[20:80, 30:70] = True  # Building region
        
        raw_output = [
            {'segmentation': mask, 'area': 2400}
        ]
        
        result = adapter.postprocess(raw_output)
        
        assert result.shape == (100, 100)
        assert result.dtype == np.uint8
        assert set(np.unique(result)).issubset({0, 255})
        assert np.sum(result == 255) == 2400  # Building pixels
    
    def test_postprocess_multiple_masks(self):
        """postprocess() should combine multiple masks using logical OR."""
        adapter = SAM2Adapter(
            checkpoint_path="/path/to/checkpoint.pth",
            model_cfg="sam2_hiera_l.yaml"
        )
        
        # Create two non-overlapping masks
        mask1 = np.zeros((100, 100), dtype=bool)
        mask1[10:30, 10:30] = True  # Top-left building
        
        mask2 = np.zeros((100, 100), dtype=bool)
        mask2[70:90, 70:90] = True  # Bottom-right building
        
        raw_output = [
            {'segmentation': mask1, 'area': 400},
            {'segmentation': mask2, 'area': 400}
        ]
        
        result = adapter.postprocess(raw_output)
        
        assert result.shape == (100, 100)
        assert result.dtype == np.uint8
        assert set(np.unique(result)).issubset({0, 255})
        # Both regions should be marked as building
        assert np.all(result[10:30, 10:30] == 255)
        assert np.all(result[70:90, 70:90] == 255)
        # Background should be 0
        assert result[0, 0] == 0
        assert result[50, 50] == 0
    
    def test_postprocess_overlapping_masks(self):
        """postprocess() should handle overlapping masks correctly."""
        adapter = SAM2Adapter(
            checkpoint_path="/path/to/checkpoint.pth",
            model_cfg="sam2_hiera_l.yaml"
        )
        
        # Create two overlapping masks
        mask1 = np.zeros((100, 100), dtype=bool)
        mask1[20:60, 20:60] = True
        
        mask2 = np.zeros((100, 100), dtype=bool)
        mask2[40:80, 40:80] = True
        
        raw_output = [
            {'segmentation': mask1, 'area': 1600},
            {'segmentation': mask2, 'area': 1600}
        ]
        
        result = adapter.postprocess(raw_output)
        
        assert result.shape == (100, 100)
        assert result.dtype == np.uint8
        # Union of both masks should be marked as building
        expected_union = np.logical_or(mask1, mask2).astype(np.uint8) * 255
        assert np.array_equal(result, expected_union)
    
    def test_postprocess_empty_masks(self):
        """postprocess() should raise error for empty mask list."""
        adapter = SAM2Adapter(
            checkpoint_path="/path/to/checkpoint.pth",
            model_cfg="sam2_hiera_l.yaml"
        )
        
        raw_output = []
        
        with pytest.raises(ValueError, match="No masks generated"):
            adapter.postprocess(raw_output)
    
    def test_postprocess_all_false_masks(self):
        """postprocess() should handle masks with all False values."""
        adapter = SAM2Adapter(
            checkpoint_path="/path/to/checkpoint.pth",
            model_cfg="sam2_hiera_l.yaml"
        )
        
        # All masks are empty (no buildings detected)
        mask1 = np.zeros((100, 100), dtype=bool)
        mask2 = np.zeros((100, 100), dtype=bool)
        
        raw_output = [
            {'segmentation': mask1, 'area': 0},
            {'segmentation': mask2, 'area': 0}
        ]
        
        result = adapter.postprocess(raw_output)
        
        assert result.shape == (100, 100)
        assert result.dtype == np.uint8
        # All pixels should be background
        assert np.all(result == 0)


class TestSAM2AdapterIntegration:
    """Test complete SAM2Adapter pipeline."""
    
    @patch('backend.models.sam2_adapter.build_sam2')
    @patch('backend.models.sam2_adapter.SAM2AutomaticMaskGenerator')
    def test_complete_segment_pipeline(self, mock_generator, mock_build):
        """Test complete segment() pipeline from image to binary mask."""
        # Setup mocks
        mock_predictor = Mock()
        
        # Create realistic mask output
        mask = np.zeros((256, 256), dtype=bool)
        mask[50:150, 50:150] = True  # Building in center
        
        mock_predictor.generate.return_value = [
            {'segmentation': mask, 'area': 10000}
        ]
        mock_generator.return_value = mock_predictor
        mock_build.return_value = Mock()
        
        # Create adapter and load
        adapter = SAM2Adapter(
            checkpoint_path="/path/to/checkpoint.pth",
            model_cfg="sam2_hiera_l.yaml"
        )
        adapter.load()
        
        # Create test image
        image = np.random.randint(0, 256, (256, 256, 3), dtype=np.uint8)
        
        # Run complete pipeline
        result = adapter.segment(image)
        
        # Verify output
        assert result.shape == (256, 256)
        assert result.dtype == np.uint8
        assert set(np.unique(result)).issubset({0, 255})
        assert np.all(result[50:150, 50:150] == 255)  # Building region
        assert result[0, 0] == 0  # Background

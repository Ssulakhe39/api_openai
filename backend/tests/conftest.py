"""
Pytest configuration and fixtures for backend tests.

This module provides common fixtures and mocking setup for all tests.
"""

import sys
from unittest.mock import MagicMock, patch
import numpy as np
import pytest

# Mock torch and other heavy dependencies before any imports
sys.modules['torch'] = MagicMock()
sys.modules['torch.nn'] = MagicMock()
sys.modules['torch.nn.functional'] = MagicMock()
sys.modules['torchvision'] = MagicMock()
sys.modules['torchvision.transforms'] = MagicMock()
sys.modules['ultralytics'] = MagicMock()
sys.modules['ultralytics.YOLO'] = MagicMock()
sys.modules['sam2'] = MagicMock()
sys.modules['sam2.build_sam'] = MagicMock()
sys.modules['sam2.sam2_image_predictor'] = MagicMock()
sys.modules['sam2.automatic_mask_generator'] = MagicMock()


@pytest.fixture()
def mock_segmentation():
    """Mock the segmentation model manager to return dummy masks.
    
    This fixture is used by API endpoint tests to avoid loading real models.
    Unit tests for the model manager itself should not use this fixture.
    """
    from backend.models.segmentation_model_manager import SegmentationModelManager
    
    def mock_segment(image: np.ndarray, model_name: str) -> np.ndarray:
        """Return a dummy binary mask matching the input image dimensions."""
        height, width = image.shape[:2]
        # Create a simple binary mask (checkerboard pattern for testing)
        mask = np.zeros((height, width), dtype=np.uint8)
        mask[::2, ::2] = 255  # Set every other pixel to 255
        return mask
    
    with patch.object(SegmentationModelManager, 'segment', side_effect=mock_segment):
        yield

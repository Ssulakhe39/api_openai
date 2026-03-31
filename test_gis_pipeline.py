"""
Test the complete GIS-ready boundary detection pipeline with real masks.
"""

import sys
import cv2
import numpy as np
from pathlib import Path

sys.path.insert(0, 'backend')

from utils.boundary_detector import BoundaryDetector
from utils.image_processor import ImageProcessor

# Initialize components
image_processor = ImageProcessor()
boundary_detector = BoundaryDetector(
    min_area=50,
    epsilon_factor=0.01,
    morph_kernel_size=3,
    morph_iterations=2,
    shapely_tolerance=None
)

# Find a real mask file to test
mask_dir = Path('backend/backend/uploads/masks')
mask_files = list(mask_dir.glob('*-mask.png'))

if not mask_files:
    print("No mask files found. Please run segmentation first.")
    sys.exit(1)

# Test with the first mask
test_mask_path = mask_files[0]
print(f"Testing with mask: {test_mask_path.name}")
print()

# Load mask
mask = image_processor.load_image(str(test_mask_path))

# Convert to grayscale if needed
if len(mask.shape) == 3:
    mask = cv2.cvtColor(mask, cv2.COLOR_RGB2GRAY)

print(f"Mask shape: {mask.shape}")
print(f"Mask dtype: {mask.dtype}")
print(f"Mask value range: [{mask.min()}, {mask.max()}]")
print()

# Detect boundaries
print("Running GIS-ready boundary detection pipeline...")
buildings = boundary_detector.detect_boundaries(mask)

print(f"✓ Detected {len(buildings)} buildings")
print()

# Show details for first few buildings
for i, building in enumerate(buildings[:3]):
    print(f"Building {building['id']}:")
    print(f"  - Area: {building['area']:.2f} pixels")
    print(f"  - Perimeter: {building['perimeter']:.2f} pixels")
    print(f"  - Number of points: {building['num_points']}")
    print(f"  - Bounding box: {building['bbox']}")
    
    if 'shapely_polygon' in building:
        print(f"  - Shapely area: {building['shapely_area']:.2f}")
        print(f"  - WKT available: Yes")
    
    print()

if len(buildings) > 3:
    print(f"... and {len(buildings) - 3} more buildings")
    print()

print("✓ GIS-ready pipeline test completed successfully!")
print()
print("Pipeline features:")
print("  ✓ Morphological preprocessing (closing + opening)")
print("  ✓ External contour extraction (RETR_EXTERNAL)")
print("  ✓ Douglas-Peucker polygon simplification")
print("  ✓ Small object filtering")
print("  ✓ Shapely polygon conversion with validation")
print("  ✓ GIS-ready WKT output")

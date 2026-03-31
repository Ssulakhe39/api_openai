"""
Convert YOLOv8 model to be compatible with current ultralytics version.
"""
import torch
import sys

# Patch torch.load to allow loading the model
_original_torch_load = torch.load

def _patched_torch_load(*args, **kwargs):
    """Patched torch.load that sets weights_only=False."""
    if 'weights_only' not in kwargs:
        kwargs['weights_only'] = False
    return _original_torch_load(*args, **kwargs)

torch.load = _patched_torch_load

from ultralytics import YOLO
import numpy as np

model_path = r"D:\model weights\best.pt"
output_path = r"D:\model weights\best_fixed.pt"

print("=" * 60)
print("YOLOv8 Model Converter")
print("=" * 60)

try:
    print(f"\n1. Loading model from: {model_path}")
    model = YOLO(model_path)
    print("   ✓ Model loaded successfully!")
    
    print(f"\n2. Model info:")
    print(f"   Task: {model.task}")
    print(f"   Names: {model.names}")
    
    print(f"\n3. Testing prediction...")
    test_image = np.random.randint(0, 255, (640, 640, 3), dtype=np.uint8)
    results = model.predict(test_image, verbose=False)
    print("   ✓ Prediction successful!")
    
    print(f"\n4. Saving fixed model to: {output_path}")
    # Save the model in the current ultralytics format
    torch.save(model.ckpt, output_path)
    print("   ✓ Model saved successfully!")
    
    print(f"\n5. Verifying fixed model...")
    model_fixed = YOLO(output_path)
    results_fixed = model_fixed.predict(test_image, verbose=False)
    print("   ✓ Fixed model works!")
    
    print("\n" + "=" * 60)
    print("SUCCESS! Use the fixed model at:")
    print(output_path)
    print("=" * 60)
    
except Exception as e:
    print(f"\n✗ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

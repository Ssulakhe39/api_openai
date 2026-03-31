"""
Rebuild YOLOv8 model by extracting weights and creating new model.
"""
import torch
import sys

# Patch torch.load
_original_torch_load = torch.load
def _patched_torch_load(*args, **kwargs):
    if 'weights_only' not in kwargs:
        kwargs['weights_only'] = False
    return _original_torch_load(*args, **kwargs)
torch.load = _patched_torch_load

from ultralytics import YOLO
import numpy as np

model_path = r"D:\model weights\best.pt"
output_path = r"D:\model weights\best_rebuilt.pt"

print("=" * 60)
print("YOLOv8 Model Rebuilder")
print("=" * 60)

try:
    print(f"\n1. Loading checkpoint...")
    checkpoint = torch.load(model_path, map_location='cpu')
    
    print(f"\n2. Creating new YOLOv8m-seg model...")
    # Create a fresh model with the same architecture
    new_model = YOLO('yolov8m-seg.pt')  # Download base model
    
    print(f"\n3. Extracting state dict from old model...")
    if 'model' in checkpoint:
        old_model = checkpoint['model']
        if hasattr(old_model, 'state_dict'):
            state_dict = old_model.state_dict()
        else:
            state_dict = old_model
    else:
        state_dict = checkpoint
    
    print(f"\n4. Loading weights into new model...")
    # Load the trained weights
    new_model.model.load_state_dict(state_dict, strict=False)
    
    print(f"\n5. Testing new model...")
    test_image = np.random.randint(0, 255, (640, 640, 3), dtype=np.uint8)
    results = new_model.predict(test_image, verbose=False)
    print("   ✓ Prediction successful!")
    
    print(f"\n6. Saving rebuilt model to: {output_path}")
    new_model.save(output_path)
    print("   ✓ Model saved!")
    
    print("\n" + "=" * 60)
    print("SUCCESS! Use the rebuilt model at:")
    print(output_path)
    print("=" * 60)
    
except Exception as e:
    print(f"\n✗ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

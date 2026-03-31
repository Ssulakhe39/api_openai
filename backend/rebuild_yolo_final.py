"""
Final attempt: Rebuild YOLOv8 model with correct number of classes.
"""
import torch
import sys
import yaml

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
output_path = r"D:\model weights\best_fixed.pt"

print("=" * 60)
print("YOLOv8 Model Final Rebuilder")
print("=" * 60)

try:
    print(f"\n1. Loading checkpoint...")
    checkpoint = torch.load(model_path, map_location='cpu')
    
    # Create a custom config with 1 class
    print(f"\n2. Creating custom model config...")
    config_path = 'yolov8m-seg-custom.yaml'
    config = {
        'nc': 1,  # number of classes
        'depth_multiple': 0.67,
        'width_multiple': 0.75,
        'backbone': [
            [-1, 1, 'Conv', [64, 3, 2]],
            [-1, 1, 'Conv', [128, 3, 2]],
            [-1, 3, 'C2f', [128, True]],
            [-1, 1, 'Conv', [256, 3, 2]],
            [-1, 6, 'C2f', [256, True]],
            [-1, 1, 'Conv', [512, 3, 2]],
            [-1, 6, 'C2f', [512, True]],
            [-1, 1, 'Conv', [768, 3, 2]],
            [-1, 3, 'C2f', [768, True]],
            [-1, 1, 'SPPF', [768, 5]]
        ],
        'head': [
            [-1, 1, 'nn.Upsample', [None, 2, 'nearest']],
            [[-1, 6], 1, 'Concat', [1]],
            [-1, 3, 'C2f', [512]],
            [-1, 1, 'nn.Upsample', [None, 2, 'nearest']],
            [[-1, 4], 1, 'Concat', [1]],
            [-1, 3, 'C2f', [256]],
            [-1, 1, 'Conv', [256, 3, 2]],
            [[-1, 12], 1, 'Concat', [1]],
            [-1, 3, 'C2f', [512]],
            [-1, 1, 'Conv', [512, 3, 2]],
            [[-1, 9], 1, 'Concat', [1]],
            [-1, 3, 'C2f', [768]],
            [[15, 18, 21], 1, 'Segment', [1, 32, 256]]  # nc=1
        ]
    }
    
    with open(config_path, 'w') as f:
        yaml.dump(config, f)
    
    print(f"\n3. Creating new model with 1 class...")
    new_model = YOLO(config_path)
    
    print(f"\n4. Loading weights...")
    if 'model' in checkpoint:
        old_model = checkpoint['model']
        if hasattr(old_model, 'state_dict'):
            state_dict = old_model.state_dict()
        else:
            state_dict = old_model
    else:
        state_dict = checkpoint
    
    # Load weights (strict=False to skip mismatched layers)
    new_model.model.load_state_dict(state_dict, strict=False)
    
    print(f"\n5. Testing model...")
    test_image = np.random.randint(0, 255, (640, 640, 3), dtype=np.uint8)
    results = new_model.predict(test_image, verbose=False)
    print("   ✓ Prediction successful!")
    
    print(f"\n6. Saving fixed model...")
    torch.save({
        'model': new_model.model,
        'train_args': checkpoint.get('train_args', {}),
        'version': checkpoint.get('version', ''),
        'date': checkpoint.get('date', ''),
    }, output_path)
    print(f"   ✓ Saved to: {output_path}")
    
    print("\n" + "=" * 60)
    print("SUCCESS! Use the fixed model at:")
    print(output_path)
    print("=" * 60)
    
except Exception as e:
    print(f"\n✗ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

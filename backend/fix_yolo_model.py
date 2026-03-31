"""
Script to inspect and fix YOLOv8 model compatibility issues.
"""
import torch
import sys

model_path = r"D:\model weights\best.pt"

print("=" * 60)
print("YOLOv8 Model Inspector")
print("=" * 60)

try:
    # Load the checkpoint
    print(f"\n1. Loading checkpoint from: {model_path}")
    checkpoint = torch.load(model_path, map_location='cpu', weights_only=False)
    
    print("\n2. Checkpoint structure:")
    if isinstance(checkpoint, dict):
        print(f"   Type: Dictionary")
        print(f"   Keys: {list(checkpoint.keys())}")
        
        # Check for version info
        if 'train_args' in checkpoint:
            print(f"\n3. Training arguments:")
            for key, value in checkpoint['train_args'].items():
                print(f"   {key}: {value}")
        
        # Check model structure
        if 'model' in checkpoint:
            model = checkpoint['model']
            print(f"\n4. Model type: {type(model)}")
            if hasattr(model, 'names'):
                print(f"   Class names: {model.names}")
            if hasattr(model, 'yaml'):
                print(f"   Model config: {model.yaml}")
    else:
        print(f"   Type: {type(checkpoint)}")
    
    print("\n5. Attempting to load with ultralytics...")
    from ultralytics import YOLO
    
    try:
        # Try loading normally
        model = YOLO(model_path)
        print("   ✓ Model loaded successfully!")
        print(f"   Task: {model.task}")
        print(f"   Model type: {type(model.model)}")
        
        # Try a test prediction
        print("\n6. Testing prediction...")
        import numpy as np
        test_image = np.random.randint(0, 255, (640, 640, 3), dtype=np.uint8)
        results = model.predict(test_image, verbose=False)
        print("   ✓ Prediction successful!")
        print(f"   Results type: {type(results)}")
        
    except Exception as e:
        print(f"   ✗ Error loading model: {e}")
        print("\n7. Attempting to export to ONNX format...")
        
        # Try to export to ONNX
        try:
            from ultralytics import YOLO
            model = YOLO(model_path)
            onnx_path = model_path.replace('.pt', '_fixed.onnx')
            model.export(format='onnx', simplify=True)
            print(f"   ✓ Model exported to ONNX: {onnx_path}")
        except Exception as e2:
            print(f"   ✗ Export failed: {e2}")

except Exception as e:
    print(f"\n✗ Fatal error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)

"""
Download YOLOv8 aerial building segmentation model from Hugging Face.
"""
from huggingface_hub import hf_hub_download
import os

# Create models directory if it doesn't exist
os.makedirs('models', exist_ok=True)

print("Downloading YOLOv8 aerial building segmentation model...")
print("Model: keremberke/yolov8s-building-segmentation")

try:
    # Download the model weights
    model_path = hf_hub_download(
        repo_id="keremberke/yolov8s-building-segmentation",
        filename="best.pt",
        local_dir="models",
        local_dir_use_symlinks=False
    )
    
    print(f"✓ Model downloaded successfully to: {model_path}")
    print(f"✓ You can now use this model with YOLOv8")
    
except Exception as e:
    print(f"✗ Error downloading model: {e}")
    print("\nTrying alternative download method...")
    
    try:
        # Try downloading without local_dir
        model_path = hf_hub_download(
            repo_id="keremberke/yolov8s-building-segmentation",
            filename="best.pt"
        )
        print(f"✓ Model downloaded to cache: {model_path}")
        
    except Exception as e2:
        print(f"✗ Alternative method also failed: {e2}")

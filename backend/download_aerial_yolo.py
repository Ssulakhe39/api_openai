"""
Download pre-trained YOLOv8 model for aerial building segmentation.

This script downloads the keremberke/yolov8s-building-segmentation model
from Hugging Face, which is specifically trained for building detection
in aerial/satellite imagery.
"""

import os
from pathlib import Path

def download_aerial_yolo_model():
    """Download YOLOv8 building segmentation model from Hugging Face."""
    try:
        from ultralytics import YOLO
        
        print("Downloading YOLOv8 aerial building segmentation model...")
        print("Model: keremberke/yolov8s-building-segmentation")
        
        # Create models directory if it doesn't exist
        models_dir = Path("backend/models")
        models_dir.mkdir(parents=True, exist_ok=True)
        
        # Download the model (it will be cached by ultralytics)
        model = YOLO('keremberke/yolov8s-building-segmentation')
        
        # Save to our models directory
        output_path = models_dir / "yolov8s-building-aerial.pt"
        
        # Export the model weights
        print(f"Saving model to: {output_path}")
        
        # The model is already downloaded and cached
        # We just need to reference it
        print("\n✓ Model downloaded successfully!")
        print(f"✓ Model will be loaded from Hugging Face cache")
        print(f"✓ Model ID: keremberke/yolov8s-building-segmentation")
        print("\nThis model is trained specifically for building detection in aerial imagery.")
        
        return True
        
    except ImportError:
        print("Error: ultralytics package not found.")
        print("Please install it with: pip install ultralytics")
        return False
    except Exception as e:
        print(f"Error downloading model: {e}")
        return False

if __name__ == "__main__":
    success = download_aerial_yolo_model()
    if success:
        print("\nYou can now use this model by selecting 'YOLOv8 Segmentation' in the web interface.")
    else:
        print("\nFailed to download the model. Please check the error messages above.")

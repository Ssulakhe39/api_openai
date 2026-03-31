"""
U-Net Aerial Building Segmentation Adapter.

This module implements a U-Net model specifically trained on aerial/satellite
imagery for building segmentation. Uses the mdranias1/satellite-building-segmentation
model from Hugging Face, trained on ISPRS Potsdam dataset.
"""

from typing import Any
import numpy as np
import torch
from PIL import Image
import logging

from .segmentation_model import SegmentationModel

logger = logging.getLogger(__name__)


class UNetAerialAdapter(SegmentationModel):
    """
    Adapter for U-Net aerial building segmentation model.
    
    This adapter uses a U-Net model trained specifically on aerial imagery
    from the ISPRS Potsdam dataset. It achieves 69% IoU for building class
    and is optimized for satellite/aerial building detection.
    
    Model: mdranias1/satellite-building-segmentation
    Architecture: Enhanced U-Net with multi-scale features
    Input: RGB images (512x512)
    Output: 6-class segmentation (we extract building class)
    """
    
    BUILDING_CLASS_ID = 1  # Buildings class in the model output
    
    def __init__(self, model_path: str = None):
        """
        Initialize UNetAerialAdapter.
        
        Args:
            model_path: Path to model weights or Hugging Face model ID
        """
        self.model_path = model_path or "mdranias1/satellite-building-segmentation"
        self.model = None
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        
        # ImageNet normalization (standard for pre-trained models)
        self.mean = torch.tensor([0.485, 0.456, 0.406]).view(3, 1, 1)
        self.std = torch.tensor([0.229, 0.224, 0.225]).view(3, 1, 1)
    
    def load(self) -> None:
        """
        Load U-Net aerial building segmentation model.
        
        Downloads model from Hugging Face if not cached locally.
        Uses segmentation-models-pytorch to create the architecture.
        
        Raises:
            Exception: If model loading fails
        """
        try:
            from huggingface_hub import hf_hub_download
            import segmentation_models_pytorch as smp
            
            logger.info(f"Loading U-Net aerial model from: {self.model_path}")
            
            # Download model from Hugging Face
            model_file = hf_hub_download(
                repo_id=self.model_path,
                filename="pytorch_model.bin"
            )
            
            # Create U-Net architecture using segmentation-models-pytorch
            # The model was trained with ResNet34 encoder and 6 output classes
            logger.info("Creating U-Net architecture with ResNet34 encoder...")
            self.model = smp.Unet(
                encoder_name='resnet34',
                encoder_weights=None,  # We'll load our custom weights
                classes=6,  # 6 classes: impervious, buildings, low veg, trees, cars, clutter
                activation=None  # No activation, we'll apply softmax in postprocess
            )
            
            # Load the state dict (weights)
            logger.info("Loading model weights...")
            checkpoint = torch.load(model_file, map_location=self.device, weights_only=False)
            
            # The checkpoint might be wrapped in a dict with 'state_dict' key
            if isinstance(checkpoint, dict):
                if 'state_dict' in checkpoint:
                    state_dict = checkpoint['state_dict']
                elif 'model_state_dict' in checkpoint:
                    state_dict = checkpoint['model_state_dict']
                else:
                    # Assume the dict itself is the state dict
                    state_dict = checkpoint
            else:
                raise Exception("Unexpected checkpoint format")
            
            # Load weights into model
            self.model.load_state_dict(state_dict)
            self.model.to(self.device)
            self.model.eval()
            
            # Move normalization tensors to device
            self.mean = self.mean.to(self.device)
            self.std = self.std.to(self.device)
            
            logger.info(f"U-Net aerial model loaded successfully on {self.device}")
            
        except ImportError as ie:
            missing_package = str(ie).split("'")[1] if "'" in str(ie) else "required package"
            raise Exception(
                f"{missing_package} package required. Install with: "
                f"pip install huggingface_hub segmentation-models-pytorch"
            )
        except Exception as e:
            raise Exception(f"Failed to load U-Net aerial model: {str(e)}")
    
    def preprocess(self, image: np.ndarray) -> torch.Tensor:
        """
        Preprocess image for U-Net model.
        
        Steps:
        1. Resize to 512x512 (model input size)
        2. Convert to tensor and normalize to [0, 1]
        3. Apply ImageNet normalization
        4. Add batch dimension
        
        Args:
            image: Input RGB image as numpy array (H, W, 3)
        
        Returns:
            Preprocessed tensor ready for model inference
        """
        # Convert to PIL for resizing
        pil_image = Image.fromarray(image)
        pil_image = pil_image.resize((512, 512), Image.BILINEAR)
        
        # Convert to tensor and normalize to [0, 1]
        image_array = np.array(pil_image)
        image_tensor = torch.from_numpy(image_array).float().permute(2, 0, 1) / 255.0
        
        # Apply ImageNet normalization
        image_tensor = (image_tensor - self.mean.cpu()) / self.std.cpu()
        
        # Add batch dimension and move to device
        image_tensor = image_tensor.unsqueeze(0).to(self.device)
        
        return image_tensor
    
    def predict(self, preprocessed_input: torch.Tensor) -> torch.Tensor:
        """
        Run U-Net inference.
        
        Args:
            preprocessed_input: Preprocessed image tensor
        
        Returns:
            Model output logits (B, C, H, W) where C=6 classes
        
        Raises:
            Exception: If prediction fails
        """
        if self.model is None:
            raise Exception("Model not loaded. Call load() first.")
        
        try:
            with torch.no_grad():
                outputs = self.model(preprocessed_input)
            return outputs
            
        except Exception as e:
            raise Exception(f"U-Net prediction failed: {str(e)}")
    
    def postprocess(self, raw_output: torch.Tensor) -> np.ndarray:
        """
        Convert U-Net output to binary building mask.
        
        The model outputs 6 classes:
        0: Impervious (roads, concrete)
        1: Buildings (our target)
        2: Low vegetation
        3: Trees
        4: Cars
        5: Clutter
        
        We extract only the building class and create a binary mask.
        
        Args:
            raw_output: Model output tensor (B, 6, H, W)
        
        Returns:
            Binary building mask (H, W) with values {0, 255}
        """
        # Apply softmax and get class predictions
        probabilities = torch.softmax(raw_output, dim=1)
        predictions = torch.argmax(probabilities, dim=1)
        
        # Extract building class (class ID = 1)
        building_mask = (predictions == self.BUILDING_CLASS_ID).cpu().numpy()[0]
        
        # Convert to uint8 binary mask
        binary_mask = (building_mask * 255).astype(np.uint8)
        
        logger.info(f"U-Net: Extracted building mask, {np.sum(building_mask)} building pixels")
        
        return binary_mask

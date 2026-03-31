"""
Quick script to inspect the U-Net model checkpoint structure.
"""
import torch
from huggingface_hub import hf_hub_download

# Download model
model_file = hf_hub_download(
    repo_id="mdranias1/satellite-building-segmentation",
    filename="pytorch_model.bin"
)

# Load checkpoint
checkpoint = torch.load(model_file, map_location='cpu', weights_only=False)

# Print structure
print("Checkpoint type:", type(checkpoint))
print("\nTop-level keys:")
if isinstance(checkpoint, dict):
    for key in checkpoint.keys():
        print(f"  - {key}")
    
    # If it has state_dict, show some weight keys
    if 'state_dict' in checkpoint:
        state_dict = checkpoint['state_dict']
    elif 'model_state_dict' in checkpoint:
        state_dict = checkpoint['model_state_dict']
    else:
        state_dict = checkpoint
    
    print(f"\nNumber of weight keys: {len(state_dict)}")
    print("\nFirst 20 weight keys:")
    for i, key in enumerate(list(state_dict.keys())[:20]):
        print(f"  {i+1}. {key}")

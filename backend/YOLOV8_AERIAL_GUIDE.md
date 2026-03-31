# YOLOv8 Aerial Building Detection Guide

## Current Status

The application currently uses **YOLOv8n-seg** with COCO pre-trained weights. This model is trained on ground-level images and performs poorly on aerial/satellite imagery.

## Why Aerial-Specific Weights Are Needed

- COCO dataset contains ground-level photos (people, cars, buildings from street view)
- Aerial imagery has different perspectives, scales, and features
- Buildings look completely different from above vs. ground level
- Pre-trained COCO weights don't recognize aerial building patterns

## Solutions for Better Aerial Building Detection

### Option 1: Use Pre-trained Aerial Models (Recommended)

Several pre-trained models exist for aerial building detection:

1. **Roboflow Universe Models**
   - Search for "aerial building detection" on Roboflow Universe
   - Many free pre-trained models available
   - Can export as YOLOv8 format

2. **Custom Training on Aerial Datasets**
   - SpaceNet Dataset (satellite building footprints)
   - INRIA Aerial Image Dataset
   - Massachusetts Buildings Dataset
   - xBD (building damage assessment)

### Option 2: Fine-tune YOLOv8 on Your Data

If you have labeled aerial images:

```python
from ultralytics import YOLO

# Load pre-trained model
model = YOLO('yolov8n-seg.pt')

# Train on your aerial dataset
model.train(
    data='aerial_buildings.yaml',  # Your dataset config
    epochs=100,
    imgsz=640,
    batch=16
)

# Save trained weights
model.save('yolov8n-aerial-buildings.pt')
```

### Option 3: Use the Model in This Application

Once you have aerial-specific weights:

1. Place the `.pt` file in `backend/models/` directory
2. Update `backend/models/segmentation_model_manager.py`:

```python
self.model_configs['yolov8'] = {
    'class': YOLOv8Adapter,
    'model_path': 'yolov8n-aerial-buildings.pt'  # Your custom weights
}
```

3. Restart the backend server

## Recommended Datasets for Training

1. **SpaceNet** - Large-scale satellite imagery with building footprints
   - https://spacenet.ai/datasets/

2. **INRIA Aerial Image Dataset** - 810 km² of aerial imagery
   - https://project.inria.fr/aerialimagelabeling/

3. **Massachusetts Buildings Dataset** - 151 aerial images
   - https://www.cs.toronto.edu/~vmnih/data/

4. **xBD (xView2)** - Building damage assessment
   - https://xview2.org/

## Current Limitations

- YOLOv8n-seg with COCO weights detects very few buildings in aerial images
- SAM2 provides better coverage but merges buildings together
- For production use, aerial-specific weights are essential

## Next Steps

1. Choose a pre-trained aerial model or dataset
2. Fine-tune YOLOv8 on aerial building data
3. Replace the model weights in the configuration
4. Test on your specific aerial imagery

## Alternative: Use SAM2 with Better Post-Processing

If training is not an option, SAM2 provides reasonable segmentation but requires:
- Better post-processing to separate merged buildings
- Watershed algorithm tuning
- Shape filtering adjustments

The boundary detection module already implements these techniques.

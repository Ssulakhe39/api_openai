# Frontend Testing Guide

## Manual Testing Steps

### Prerequisites
1. Backend server must be running on http://localhost:8000
2. Frontend dev server must be running (typically http://localhost:5173)

### Test Workflow

#### 1. Test Image Upload (Tasks 9.1-9.2)
- [ ] Open the application in a browser
- [ ] Click the file input and select a JPG/PNG/TIFF image
- [ ] Verify the file name appears in the upload status
- [ ] Click "Upload" button
- [ ] Verify "Uploading..." status appears
- [ ] Verify uploaded image appears in the "Original Image" panel
- [ ] Verify upload success message shows image dimensions

**Error Cases:**
- [ ] Try uploading a non-image file (e.g., .txt) - should show error
- [ ] Try uploading without selecting a file - should show error

#### 2. Test Model Selection (Tasks 10.1-10.2)
- [ ] Verify dropdown shows three models: SAM2, YOLOv8, U-Net
- [ ] Select each model and verify selection updates
- [ ] Hover over options to see descriptions (if implemented)
- [ ] Verify first model is selected by default

#### 3. Test Segmentation Execution (Tasks 11.1-11.2)
- [ ] Verify "Run Segmentation" button is disabled initially
- [ ] Upload an image
- [ ] Verify button becomes enabled after upload
- [ ] Click "Run Segmentation"
- [ ] Verify loading indicator appears
- [ ] Verify button is disabled during processing
- [ ] Wait for segmentation to complete

**Error Cases:**
- [ ] Try clicking button without image - should be disabled
- [ ] Disconnect network during segmentation - should show error

#### 4. Test Visualization (Tasks 12.1-12.3)
After successful segmentation:
- [ ] Verify three panels are displayed side-by-side
- [ ] Verify "Original Image" panel shows the uploaded image
- [ ] Verify "Segmentation Mask" panel shows black/white mask
- [ ] Verify "Overlay" panel shows original image with red overlay on buildings
- [ ] Verify all three panels have consistent dimensions
- [ ] Verify overlay has transparency (original image visible underneath)

#### 5. Test State Management and UI Feedback (Task 13)
- [ ] Verify buttons show hover effects
- [ ] Verify buttons show active state when clicked
- [ ] Verify file input changes color when file selected
- [ ] Verify model dropdown shows visual feedback on change
- [ ] Verify error banner appears for errors
- [ ] Verify error banner auto-hides after 5 seconds
- [ ] Verify loading spinner shows during processing

#### 6. Test Complete Workflow Integration (Tasks 14.1-14.2)
- [ ] Upload image → Select model → Run segmentation → View results
- [ ] Upload different image and run segmentation again
- [ ] Switch models and run segmentation on same image
- [ ] Verify state is preserved across operations
- [ ] Check browser console for any errors

### Browser Compatibility
Test in:
- [ ] Chrome/Edge
- [ ] Firefox
- [ ] Safari (if available)

### Performance
- [ ] Test with small image (< 1MB)
- [ ] Test with large image (10-20MB)
- [ ] Verify processing time is displayed
- [ ] Verify UI remains responsive during processing

## Automated Testing

Run unit tests:
```bash
cd frontend
npm test
```

Run property-based tests:
```bash
npm test -- --testNamePattern="Property"
```

## Known Limitations
- CORS must be configured correctly on backend
- Large images may take longer to process
- Overlay generation requires Canvas API support

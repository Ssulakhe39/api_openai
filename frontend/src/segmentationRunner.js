/**
 * SegmentationRunner - Triggers segmentation and handles response
 */
export class SegmentationRunner {
  constructor(imageUploader, modelSelector) {
    this.imageUploader = imageUploader;
    this.modelSelector = modelSelector;
    this.segmentButton = document.getElementById('segment-button');
    this.loadingIndicator = document.getElementById('loading-indicator');
    this.segmentationResult = null;

    // Ensure loading indicator is hidden on init (clears stale state)
    this.loadingIndicator.style.display = 'none';

    this.setupEventListeners();
  }

  setupEventListeners() {
    this.segmentButton.addEventListener('click', () => this.handleSegmentation());
    
    // Enable button when image is uploaded
    window.addEventListener('imageUploaded', () => {
      this.updateButtonState();
    });
    
    // Update button state when model is selected
    window.addEventListener('modelSelected', () => {
      this.updateButtonState();
    });
  }

  updateButtonState() {
    this.segmentButton.disabled = !this.canRunSegmentation();
  }

  /**
   * Check if segmentation can run (image uploaded, model selected)
   * @returns {boolean}
   */
  canRunSegmentation() {
    const hasImage = this.imageUploader.getImageId() !== null;
    const hasModel = this.modelSelector.getSelectedModel() !== null;
    return hasImage && hasModel;
  }

  async handleSegmentation() {
    if (!this.canRunSegmentation()) {
      this.showError('Please upload an image and select a model first.');
      return;
    }
    
    const imageId = this.imageUploader.getImageId();
    const modelName = this.modelSelector.getSelectedModel();
    
    try {
      const result = await this.runSegmentation(imageId, modelName);
      this.segmentationResult = result;
      
      // Enable boundary buttons now that a mask exists
      const boundaryBtn    = document.getElementById('boundary-button');
      const gptBoundaryBtn = document.getElementById('gpt-boundary-button');
      if (boundaryBtn)    boundaryBtn.disabled    = false;
      if (gptBoundaryBtn) gptBoundaryBtn.disabled = false;

      // Trigger custom event for visualization
      window.dispatchEvent(new CustomEvent('segmentationComplete', { 
        detail: result 
      }));
      
    } catch (error) {
      this.showError(error.message);
    }
  }

  /**
   * Run segmentation on uploaded image
   * @param {string} imageId - ID of uploaded image
   * @param {string} modelName - Name of model to use
   * @returns {Promise<Object>} - Segmentation result with maskUrl, processingTime, modelUsed
   */
  async runSegmentation(imageId, modelName) {
    // Show loading indicator
    this.segmentButton.disabled = true;
    this.loadingIndicator.style.display = 'block';

    // Elapsed time counter so user sees progress
    let elapsed = 0;
    const loadingSpan = this.loadingIndicator.querySelector('span');
    const timer = setInterval(() => {
      elapsed++;
      if (loadingSpan) loadingSpan.textContent = `Processing segmentation, please wait... (${elapsed}s)`;
    }, 1000);

    try {
      // 5 minute timeout for large model inference
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 300000);

      const response = await fetch('http://localhost:8000/segment', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          image_id: imageId,
          model: modelName
        }),
        signal: controller.signal
      });
      clearTimeout(timeoutId);
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Segmentation failed');
      }
      
      const data = await response.json();
      
      return {
        maskUrl: `http://localhost:8000${data.mask_url}`,
        maskBase64: data.mask_base64,
        processingTime: data.processing_time,
        modelUsed: data.model_used
      };
      
    } catch (error) {
      if (error.message.includes('Failed to fetch')) {
        throw new Error('Segmentation failed. Please check your connection and try again.');
      }
      throw error;
    } finally {
      // Hide loading indicator and clear timer
      clearInterval(timer);
      if (loadingSpan) loadingSpan.textContent = 'Processing segmentation, please wait...';
      this.loadingIndicator.style.display = 'none';
      this.segmentButton.disabled = false;
    }
  }

  showError(message) {
    const errorBanner = document.getElementById('error-banner');
    errorBanner.textContent = message;
    errorBanner.style.display = 'block';
    
    setTimeout(() => {
      errorBanner.style.display = 'none';
    }, 5000);
  }

  getSegmentationResult() {
    return this.segmentationResult;
  }
}

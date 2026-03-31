/**
 * Main Application Entry Point
 * Wires together all frontend components
 */
import { ImageUploader } from './imageUploader.js';
import { ModelSelector } from './modelSelector.js';
import { SegmentationRunner } from './segmentationRunner.js';
import { VisualizationPanel } from './visualizationPanel.js';
import { AppState } from './appState.js';
import { BoundaryDetector } from './boundaryDetector.js';
import { GPTBoundaryDetector } from './gptBoundaryDetector.js';

/**
 * Main Application Class
 */
class AerialSegmentationApp {
  constructor() {
    this.appState = new AppState();
    this.imageUploader = new ImageUploader();
    this.modelSelector = new ModelSelector();
    this.segmentationRunner = new SegmentationRunner(
      this.imageUploader,
      this.modelSelector
    );
    this.visualizationPanel = new VisualizationPanel(this.imageUploader);
    this.boundaryDetector = new BoundaryDetector(
      this.imageUploader,
      this.modelSelector
    );
    this.gptBoundaryDetector = new GPTBoundaryDetector(
      this.imageUploader,
      this.modelSelector
    );
    
    this.init();
  }

  init() {
    // Initialize UI feedback
    this.appState.initializeUIFeedback();
    
    // Set up workflow coordination
    this.setupWorkflowHandlers();
    
    console.log('Aerial Image Segmentation App initialized');
  }

  setupWorkflowHandlers() {
    // Handle image upload success
    window.addEventListener('imageUploaded', (event) => {
      console.log('Image uploaded:', event.detail);
      
      // Enable segmentation button if model is selected
      if (this.modelSelector.getSelectedModel()) {
        document.getElementById('segment-button').disabled = false;
      }
    });
    
    // Handle model selection
    window.addEventListener('modelSelected', (event) => {
      console.log('Model selected:', event.detail.modelName);
      
      // Enable segmentation button if image is uploaded
      if (this.imageUploader.getImageId()) {
        document.getElementById('segment-button').disabled = false;
      }
    });
    
    // Handle segmentation completion
    window.addEventListener('segmentationComplete', (event) => {
      console.log('Segmentation complete:', event.detail);
      console.log(`Processing time: ${event.detail.processingTime.toFixed(2)}s`);
    });
    
    // Handle boundary detection completion
    window.addEventListener('boundariesDetected', (event) => {
      console.log('Boundaries detected:', event.detail);
      console.log(`Total buildings: ${event.detail.totalBuildings}`);
    });
    
    // Handle state changes
    window.addEventListener('stateChanged', (event) => {
      console.log('State changed:', event.detail);
    });
  }
}

// Initialize app when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    new AerialSegmentationApp();
  });
} else {
  new AerialSegmentationApp();
}

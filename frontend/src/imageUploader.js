/**
 * ImageUploader - Handles file selection, validation, and upload to backend
 */
export class ImageUploader {
  constructor() {
    this.fileInput = document.getElementById('image-input');
    this.uploadButton = document.getElementById('upload-button');
    this.uploadStatus = document.getElementById('upload-status');
    this.originalPanel = document.getElementById('original-panel');
    this.uploadedImageData = null;
    this.imageId = null;
    
    this.setupEventListeners();
  }

  setupEventListeners() {
    this.uploadButton.addEventListener('click', () => this.handleUpload());
    this.fileInput.addEventListener('change', () => this.handleFileSelect());
  }

  handleFileSelect() {
    const file = this.fileInput.files[0];
    if (file) {
      const validation = this.validateFile(file);
      if (!validation.valid) {
        this.showError(validation.error);
        this.fileInput.value = '';
      } else {
        this.uploadStatus.textContent = `Selected: ${file.name}`;
        this.uploadStatus.style.color = '#27ae60';
      }
    }
  }

  /**
   * Validate file format before upload
   * @param {File} file - The file to validate
   * @returns {Object} - {valid: boolean, error?: string}
   */
  validateFile(file) {
    const validExtensions = ['.jpg', '.jpeg', '.png', '.tiff', '.tif'];
    const fileName = file.name.toLowerCase();
    const hasValidExtension = validExtensions.some(ext => fileName.endsWith(ext));
    
    if (!hasValidExtension) {
      return {
        valid: false,
        error: 'Unsupported file format. Please upload JPG, PNG, or TIFF images.'
      };
    }
    
    // Check if file is not empty
    if (file.size === 0) {
      return {
        valid: false,
        error: 'File is empty. Please select a valid image file.'
      };
    }
    
    // Check file size (max 50MB)
    const maxSize = 50 * 1024 * 1024; // 50MB in bytes
    if (file.size > maxSize) {
      return {
        valid: false,
        error: 'Image file is too large. Maximum size is 50MB.'
      };
    }
    
    return { valid: true };
  }

  /**
   * Upload image file to backend
   * @param {File} file - The file to upload
   * @returns {Promise<Object>} - Upload response with imageId, imageUrl, width, height
   */
  async uploadImage(file) {
    const formData = new FormData();
    formData.append('file', file);
    
    try {
      const response = await fetch('http://localhost:8000/upload', {
        method: 'POST',
        body: formData
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Upload failed');
      }
      
      const data = await response.json();
      return data;
    } catch (error) {
      if (error.message.includes('Failed to fetch')) {
        throw new Error('Upload failed. Please check your connection and try again.');
      }
      throw error;
    }
  }

  async handleUpload() {
    const file = this.fileInput.files[0];
    
    if (!file) {
      this.showError('Please select an image file first.');
      return;
    }
    
    const validation = this.validateFile(file);
    if (!validation.valid) {
      this.showError(validation.error);
      return;
    }
    
    // Show uploading status
    this.uploadButton.disabled = true;
    this.uploadStatus.textContent = 'Uploading...';
    this.uploadStatus.style.color = '#3498db';
    
    try {
      const response = await this.uploadImage(file);
      this.imageId = response.image_id;
      this.uploadedImageData = response;
      
      // Display the uploaded image
      this.displayImage(`http://localhost:8000${response.image_url}`);
      
      this.uploadStatus.textContent = `Upload successful! (${response.width}x${response.height})`;
      this.uploadStatus.style.color = '#27ae60';
      
      // Trigger custom event for other components
      window.dispatchEvent(new CustomEvent('imageUploaded', { 
        detail: response 
      }));
      
    } catch (error) {
      this.showError(error.message);
      this.uploadStatus.textContent = '';
    } finally {
      this.uploadButton.disabled = false;
    }
  }

  /**
   * Display uploaded image in UI
   * @param {string} imageUrl - URL of the image to display
   */
  displayImage(imageUrl) {
    // Clear placeholder
    this.originalPanel.innerHTML = '';
    
    // Create and display image
    const img = document.createElement('img');
    img.src = imageUrl;
    img.alt = 'Uploaded aerial image';
    img.style.maxWidth = '100%';
    img.style.maxHeight = '500px';
    img.style.objectFit = 'contain';
    
    this.originalPanel.appendChild(img);
  }

  showError(message) {
    const errorBanner = document.getElementById('error-banner');
    errorBanner.textContent = message;
    errorBanner.style.display = 'block';
    
    // Hide error after 5 seconds
    setTimeout(() => {
      errorBanner.style.display = 'none';
    }, 5000);
  }

  getImageId() {
    return this.imageId;
  }

  getUploadedImageData() {
    return this.uploadedImageData;
  }

  getOriginalFilename() {
    const file = this.fileInput.files[0];
    if (!file) return 'output';
    // Strip extension: "tile_01.png" -> "tile_01"
    return file.name.replace(/\.[^/.]+$/, '');
  }
}

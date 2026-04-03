// BHUMI AI - Main Application Entry Point
// Single Page Application with sidebar navigation

import { ImageUploader } from './imageUploader.js';
import { ModelSelector } from './modelSelector.js';
import { SegmentationRunner } from './segmentationRunner.js';
import { BoundaryDetector } from './boundaryDetector.js';
import { GPTBoundaryDetector } from './gptBoundaryDetector.js';
import { BatchProcessor } from './batchProcessor.js';
import { Dashboard } from './dashboard.js';

// Main Application Class
class BhumiAIApp {
  constructor() {
    this.currentPage = 'dashboard';
    this.currentView = 'original'; // For single processing viewer
    
    // Will be initialized when pages are loaded
    this.imageUploader = null;
    this.modelSelector = null;
    this.segmentationRunner = null;
    this.boundaryDetector = null;
    this.gptBoundaryDetector = null;
    this.batchProcessor = null;
    this.dashboard = null;
    
    this.init();
  }

  init() {
    // Set up user info
    this.setupUserInfo();
    
    // Set up navigation
    this.setupNavigation();
    
    // Set up theme switcher
    this.setupThemeSwitcher();
    
    // Set up settings tabs
    this.setupSettingsTabs();
    
    // Initialize dashboard
    this.dashboard = new Dashboard();
    this.dashboard.init();
    
    // Set up sign out
    this.setupSignOut();
    
    // Load dashboard stats
    this.loadDashboardStats();
    
    // Load initial page content
    this.loadRecentJobs();
    
    console.log('BHUMI AI Application initialized');
  }

  setupUserInfo() {
    const username = sessionStorage.getItem('auth_user') || 'operator';
    const email = `${username}@bhumi.ai`;
    const initials = username.substring(0, 2).toUpperCase();
    
    // Update sidebar user info
    const userNameEl = document.getElementById('userName');
    const userEmailEl = document.getElementById('userEmail');
    const userAvatarEl = document.getElementById('userAvatar');
    
    if (userNameEl) userNameEl.textContent = username;
    if (userEmailEl) userEmailEl.textContent = email;
    if (userAvatarEl) userAvatarEl.textContent = initials;
    
    // Update profile page
    const profileNameEl = document.getElementById('profileName');
    const profileEmailEl = document.getElementById('profileEmail');
    const profileAvatarEl = document.getElementById('profileAvatar');
    
    if (profileNameEl) profileNameEl.textContent = username.charAt(0).toUpperCase() + username.slice(1);
    if (profileEmailEl) profileEmailEl.textContent = `📧 ${email}`;
    if (profileAvatarEl) profileAvatarEl.textContent = initials;
    
    // Set member since date
    const loginTime = sessionStorage.getItem('auth_login_time');
    const memberSince = loginTime ? new Date(parseInt(loginTime)).toISOString().split('T')[0] : '2023-01-15';
    const memberSinceEl = document.getElementById('profileMemberSince');
    if (memberSinceEl) memberSinceEl.textContent = memberSince;
    
    // Update settings fields
    const settingsUsernameEl = document.getElementById('settingsUsername');
    const settingsEmailEl = document.getElementById('settingsEmail');
    if (settingsUsernameEl) settingsUsernameEl.value = username;
    if (settingsEmailEl) settingsEmailEl.value = email;
  }

  setupNavigation() {
    const navItems = document.querySelectorAll('.sidebar-nav-item');
    console.log('Setting up navigation, found', navItems.length, 'nav items');
    
    navItems.forEach(item => {
      item.addEventListener('click', (e) => {
        e.preventDefault();
        const page = item.dataset.page;
        console.log('=== NAV ITEM CLICKED ===', page);
        this.navigateToPage(page);
      });
    });
  }

  navigateToPage(page) {
    console.log('=== NAVIGATION START ===');
    console.log('Navigating to page:', page);
    
    try {
      // Update active nav item
      document.querySelectorAll('.sidebar-nav-item').forEach(item => {
        item.classList.remove('active');
        if (item.dataset.page === page) {
          item.classList.add('active');
        }
      });
      console.log('Nav items updated');
      
      // Update page sections
      document.querySelectorAll('.page-section').forEach(section => {
        section.classList.remove('active');
      });
      console.log('All page sections hidden');
      
      const pageSection = document.getElementById(`page-${page}`);
      console.log('Looking for page section:', `page-${page}`, 'Found:', !!pageSection);
      
      if (pageSection) {
        pageSection.classList.add('active');
        console.log('Page section activated');
      } else {
        console.error('Page section not found:', `page-${page}`);
        return;
      }
      
      // Update breadcrumb
      const pageNames = {
        dashboard: 'Dashboard',
        single: 'Single Processing',
        batch: 'Batch Processing',
        history: 'Processing History',
        settings: 'Settings & Profile'
      };
      const currentPageEl = document.getElementById('currentPage');
      if (currentPageEl) currentPageEl.textContent = pageNames[page] || page;
      console.log('Breadcrumb updated');
      
      this.currentPage = page;
      
      // Load page-specific content
      if (page === 'single') {
        console.log('Loading Single Processing page...');
        this.loadSingleProcessingPage();
      } else if (page === 'batch') {
        console.log('Loading Batch Processing page...');
        this.loadBatchProcessingPage();
      } else if (page === 'history') {
        console.log('Loading History page...');
        this.loadHistoryPage();
      }
      
      console.log('=== NAVIGATION COMPLETE ===');
    } catch (error) {
      console.error('=== NAVIGATION ERROR ===');
      console.error('Error in navigateToPage:', error);
      console.error('Stack:', error.stack);
    }
  }

  loadSingleProcessingPage() {
    console.log('=== LOAD SINGLE PROCESSING PAGE START ===');
    try {
      const container = document.getElementById('singleProcessingContent');
      console.log('Container found:', !!container);
      
      if (!container) {
        console.error('singleProcessingContent container not found');
        alert('ERROR: singleProcessingContent container not found');
        return;
      }
      
      if (container.children.length > 0) {
        console.log('Single Processing page already loaded');
        return; // Already loaded
      }
      
      console.log('Creating Single Processing page HTML...');
    container.innerHTML = `
      <div class="processing-grid">
        <div class="processing-sidebar">
          <div class="card">
            <h3 class="card-title">SOURCE MATERIAL</h3>
            <div style="margin-top: var(--spacing-md);">
              <div class="upload-zone" id="singleUploadZone">
                <div class="upload-zone-icon">📁</div>
                <div class="upload-zone-title">Drop image here</div>
                <div class="upload-zone-subtitle">JPG, PNG, TIFF (Max 50MB)</div>
                <input type="file" id="image-input" accept=".jpg,.jpeg,.png,.tiff,.tif" style="display: none;">
                <button class="btn btn-secondary" id="browseImageBtn">Browse Files</button>
              </div>
              <div id="upload-status" style="margin-top: var(--spacing-md); font-size: 0.875rem; color: var(--text-secondary);"></div>
            </div>
          </div>
          
          <div class="card">
            <h3 class="card-title">INTELLIGENCE MODEL</h3>
            <div id="model-select" style="margin-top: var(--spacing-md); display: flex; flex-direction: column; gap: var(--spacing-sm);">
              <div class="model-card" data-model="yolov8">
                <div class="model-card-header">
                  <div class="model-card-radio"></div>
                  <span class="model-card-title">YOLOv8</span>
                  <span class="model-card-version">v8.8</span>
                </div>
                <p class="model-card-description">Fastest speed for dense urban</p>
              </div>
              <div class="model-card" data-model="maskrcnn-custom">
                <div class="model-card-header">
                  <div class="model-card-radio"></div>
                  <span class="model-card-title">Mask R-CNN</span>
                  <span class="model-card-version">v3.4</span>
                </div>
                <p class="model-card-description">Complex irregular boundaries</p>
              </div>
            </div>
          </div>
          
          <button class="btn btn-primary" id="segment-button" disabled style="width: 100%;">
            <span>🔍</span>
            <span>Run Segmentation</span>
          </button>
          
          <button class="btn btn-secondary" id="gpt-boundary-button" disabled style="width: 100%;">
            <span>📐</span>
            <span>Extract Boundaries</span>
          </button>
          
          <div id="loading-indicator" style="display: none; padding: var(--spacing-md); background: var(--status-info-bg); border: 1px solid var(--status-info); border-radius: var(--radius-md); color: var(--status-info); font-size: 0.875rem; text-align: center;">
            <div class="spinner" style="margin: 0 auto var(--spacing-sm);"></div>
            <span>Processing...</span>
          </div>
          
          <div id="boundary-status" style="margin-top: var(--spacing-sm); font-size: 0.875rem;"></div>
          <div id="gpt-status" style="margin-top: var(--spacing-sm); font-size: 0.875rem;"></div>
        </div>
        
        <div class="processing-main">
          <div style="display: flex; gap: var(--spacing-sm); margin-bottom: var(--spacing-md); border-bottom: 1px solid var(--border-primary);">
            <button class="btn btn-secondary view-tab active" data-view="original">Original</button>
            <button class="btn btn-secondary view-tab" data-view="mask">Mask</button>
            <button class="btn btn-secondary view-tab" data-view="overlay">Overlay</button>
          </div>
          
          <div class="image-viewer" id="imageViewer">
            <div class="image-viewer-placeholder">
              <div class="image-viewer-placeholder-icon">🖼️</div>
              <p>Upload an image to begin processing</p>
            </div>
          </div>
          
          <!-- Hidden panels for compatibility -->
          <div id="original-panel" style="display: none;"></div>
          <div id="mask-panel" style="display: none;"></div>
          <div id="overlay-panel" style="display: none;"></div>
          
          <!-- GPT Panel for boundary detection -->
          <div id="gpt-panel-wrapper" style="display: none;">
            <div id="gpt-panel" style="background: var(--bg-card); border: 1px solid var(--border-primary); border-radius: var(--radius-lg); padding: var(--spacing-lg); margin-top: var(--spacing-lg);"></div>
            <div id="gpt-info-bar" style="display: none; margin-top: var(--spacing-sm); font-size: 0.875rem; color: var(--text-secondary);"></div>
            <div id="gpt-edit-bar" style="display: none; margin-top: var(--spacing-sm); display: flex; gap: var(--spacing-sm);">
              <button id="gpt-edit-button" class="btn btn-secondary">Edit Polygons</button>
              <button id="gpt-draw-button" class="btn btn-secondary" style="display: none;">Draw Polygon</button>
              <button id="gpt-delete-button" class="btn btn-danger" style="display: none;">Delete Polygon</button>
              <button id="gpt-done-button" class="btn btn-success" style="display: none;">Done Editing</button>
            </div>
          </div>
          
          <div id="detection-results" style="margin-top: var(--spacing-lg); display: none;">
            <div class="card">
              <h3 class="card-title">DETECTION RESULTS</h3>
              <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: var(--spacing-md); margin-top: var(--spacing-md);">
                <div>
                  <div style="font-size: 0.75rem; color: var(--text-tertiary); margin-bottom: var(--spacing-xs);">BUILDINGS DETECTED</div>
                  <div style="font-size: 1.5rem; font-weight: 700; color: var(--primary-cyan);" id="buildingCount">0</div>
                </div>
                <div>
                  <div style="font-size: 0.75rem; color: var(--text-tertiary); margin-bottom: var(--spacing-xs);">AVG CONFIDENCE</div>
                  <div style="font-size: 1.5rem; font-weight: 700; color: var(--status-success);" id="avgConfidence">0%</div>
                </div>
                <div>
                  <div style="font-size: 0.75rem; color: var(--text-tertiary); margin-bottom: var(--spacing-xs);">PROC. TIME</div>
                  <div style="font-size: 1.5rem; font-weight: 700; color: var(--text-primary);" id="procTime">0s</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <div id="error-banner" style="display: none; margin-top: var(--spacing-lg); padding: var(--spacing-md); background: var(--status-error-bg); border: 1px solid var(--status-error); color: var(--status-error); border-radius: var(--radius-md);"></div>
    `;
    
    console.log('Single Processing HTML created, initializing components...');
    
    // Initialize components for single processing
    try {
      this.initializeSingleProcessing();
      console.log('=== SINGLE PROCESSING PAGE LOADED SUCCESSFULLY ===');
    } catch (error) {
      console.error('=== ERROR INITIALIZING SINGLE PROCESSING ===');
      console.error('Error:', error);
      console.error('Stack:', error.stack);
      alert('ERROR initializing Single Processing: ' + error.message);
    }
  }

  initializeSingleProcessing() {
    console.log('=== INITIALIZING SINGLE PROCESSING ===');
    
    try {
      // Initialize components
      console.log('Creating ImageUploader...');
      this.imageUploader = new ImageUploader();
      console.log('ImageUploader created successfully');
      
      console.log('Creating ModelSelector...');
      this.modelSelector = new ModelSelector();
      console.log('ModelSelector created successfully');
      
      console.log('Creating SegmentationRunner...');
      this.segmentationRunner = new SegmentationRunner(this.imageUploader, this.modelSelector);
      console.log('SegmentationRunner created successfully');
      
      console.log('Creating BoundaryDetector...');
      this.boundaryDetector = new BoundaryDetector(this.imageUploader, this.modelSelector);
      console.log('BoundaryDetector created successfully');
      
      console.log('Creating GPTBoundaryDetector...');
      this.gptBoundaryDetector = new GPTBoundaryDetector(this.imageUploader, this.modelSelector);
      console.log('GPTBoundaryDetector created successfully');
    } catch (error) {
      console.error('=== ERROR CREATING COMPONENTS ===');
      console.error('Error:', error);
      console.error('Stack:', error.stack);
      throw error;
    }
    
    // Set up upload zone
    console.log('Setting up upload zone...');
    const uploadZone = document.getElementById('singleUploadZone');
    const fileInput = document.getElementById('image-input');
    const browseBtn = document.getElementById('browseImageBtn');
    
    console.log('Upload zone elements:', { uploadZone: !!uploadZone, fileInput: !!fileInput, browseBtn: !!browseBtn });
    
    if (browseBtn && fileInput) {
      browseBtn.addEventListener('click', () => fileInput.click());
      console.log('Browse button listener added');
    }
    
    if (fileInput) {
      // Handle file selection - automatically upload when file is selected
      fileInput.addEventListener('change', async () => {
        console.log('File input changed');
        const file = fileInput.files[0];
        if (!file) return;
        
        // Validate file
        const validation = this.imageUploader.validateFile(file);
        if (!validation.valid) {
          this.showError(validation.error);
          fileInput.value = '';
          return;
        }
        
        // Show uploading status
        const statusEl = document.getElementById('upload-status');
        if (statusEl) {
          statusEl.textContent = `Uploading ${file.name}...`;
          statusEl.style.color = 'var(--status-info)';
        }
        
        try {
          // Upload the file
          const response = await this.imageUploader.uploadImage(file);
          this.imageUploader.imageId = response.image_id;
          this.imageUploader.uploadedImageData = response;
          
          // Update status
          if (statusEl) {
            statusEl.textContent = `✓ Uploaded: ${file.name} (${response.width}x${response.height})`;
            statusEl.style.color = 'var(--status-success)';
          }
          
          // Display image in viewer
          const viewer = document.getElementById('imageViewer');
          if (viewer) {
            viewer.innerHTML = `<img src="${response.image_url}" alt="Uploaded image" style="max-width: 100%; max-height: 70vh; object-fit: contain; border-radius: var(--radius-md);">`;
          }
          
          // Also update the hidden original panel for compatibility
          const originalPanel = document.getElementById('original-panel');
          if (originalPanel) {
            originalPanel.innerHTML = `<img src="${response.image_url}" alt="Uploaded image" style="max-width: 100%; max-height: 500px; object-fit: contain;">`;
          }
          
          // Trigger event
          window.dispatchEvent(new CustomEvent('imageUploaded', { 
            detail: response 
          }));
          
        } catch (error) {
          this.showError(error.message);
          if (statusEl) {
            statusEl.textContent = '';
          }
        }
      });
      console.log('File input listener added');
    }
    
    if (uploadZone && fileInput) {
      uploadZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadZone.classList.add('dragover');
      });
      
      uploadZone.addEventListener('dragleave', () => {
        uploadZone.classList.remove('dragover');
      });
      
      uploadZone.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadZone.classList.remove('dragover');
        if (e.dataTransfer.files.length > 0) {
          fileInput.files = e.dataTransfer.files;
          // Trigger change event
          const event = new Event('change', { bubbles: true });
          fileInput.dispatchEvent(event);
        }
      });
      console.log('Drag and drop listeners added');
    }
    
    // Set up model selection
    console.log('Setting up model selection...');
    document.querySelectorAll('.model-card').forEach(card => {
      card.addEventListener('click', () => {
        document.querySelectorAll('.model-card').forEach(c => c.classList.remove('selected'));
        card.classList.add('selected');
        const model = card.dataset.model;
        this.modelSelector.setSelectedModel(model);
      });
    });
    console.log('Model selection listeners added');
    
    // Set up view tabs
    console.log('Setting up view tabs...');
    document.querySelectorAll('.view-tab').forEach(tab => {
      tab.addEventListener('click', () => {
        document.querySelectorAll('.view-tab').forEach(t => t.classList.remove('active'));
        tab.classList.add('active');
        this.currentView = tab.dataset.view;
        this.updateImageViewer();
      });
    });
    console.log('View tab listeners added');
    
    // Initialize existing components (but don't call setupEventListeners again for imageUploader)
    console.log('Initializing component event listeners...');
    try {
      this.modelSelector.init();
      console.log('ModelSelector initialized');
    } catch (error) {
      console.error('Error initializing ModelSelector:', error);
    }
    
    try {
      this.segmentationRunner.setupEventListeners();
      console.log('SegmentationRunner event listeners set up');
    } catch (error) {
      console.error('Error setting up SegmentationRunner:', error);
    }
    
    try {
      this.boundaryDetector.setupEventListeners();
      console.log('BoundaryDetector event listeners set up');
    } catch (error) {
      console.error('Error setting up BoundaryDetector:', error);
    }
    
    // GPTBoundaryDetector uses event delegation, so it should work automatically
    // But let's make sure it's initialized
    console.log('GPTBoundaryDetector initialized:', this.gptBoundaryDetector);
    
    // Set up workflow handlers
    console.log('Setting up workflow handlers...');
    this.setupWorkflowHandlers();
    
    console.log('=== SINGLE PROCESSING INITIALIZATION COMPLETE ===');
  }
  
  showError(message) {
    const errorBanner = document.getElementById('error-banner');
    if (errorBanner) {
      errorBanner.textContent = message;
      errorBanner.style.display = 'block';
      
      setTimeout(() => {
        errorBanner.style.display = 'none';
      }, 5000);
    }
  }

  updateImageViewer() {
    const viewer = document.getElementById('imageViewer');
    if (!viewer) return;
    
    const originalPanel = document.getElementById('original-panel');
    const maskPanel = document.getElementById('mask-panel');
    const overlayPanel = document.getElementById('overlay-panel');
    const gptPanel = document.getElementById('gpt-panel');
    
    viewer.innerHTML = '';
    
    if (this.currentView === 'original' && originalPanel && originalPanel.children.length > 0) {
      viewer.appendChild(originalPanel.children[0].cloneNode(true));
    } else if (this.currentView === 'mask' && maskPanel && maskPanel.children.length > 0) {
      viewer.appendChild(maskPanel.children[0].cloneNode(true));
    } else if (this.currentView === 'overlay' && overlayPanel && overlayPanel.children.length > 0) {
      viewer.appendChild(overlayPanel.children[0].cloneNode(true));
    } else if (gptPanel && gptPanel.children.length > 0) {
      // Show GPT panel if available
      const gptContent = gptPanel.cloneNode(true);
      gptContent.style.display = 'block';
      viewer.appendChild(gptContent);
    } else {
      viewer.innerHTML = `
        <div class="image-viewer-placeholder">
          <div class="image-viewer-placeholder-icon">🖼️</div>
          <p>No ${this.currentView} available yet</p>
        </div>
      `;
    }
  }

  loadBatchProcessingPage() {
    const container = document.getElementById('batchProcessingContent');
    if (!container) return;
    
    if (container.children.length > 0) return; // Already loaded
    
    // Initialize batch processor
    if (!this.batchProcessor) {
      this.batchProcessor = new BatchProcessor(this.modelSelector || new ModelSelector());
    }
    this.batchProcessor.init();
  }

  loadHistoryPage() {
    this.loadProcessingHistory();
  }

  async loadProcessingHistory() {
    const tbody = document.getElementById('historyTableBody');
    if (!tbody) return;
    
    tbody.innerHTML = `
      <tr>
        <td colspan="7" style="text-align: center; padding: 3rem; color: var(--text-tertiary);">
          <div class="empty-state">
            <div class="empty-state-icon">📋</div>
            <div class="empty-state-title">No processing history yet</div>
            <div class="empty-state-description">Start processing images to see them here</div>
          </div>
        </td>
      </tr>
    `;
  }

  setupThemeSwitcher() {
    const themeOptions = document.querySelectorAll('.theme-option');
    
    themeOptions.forEach(option => {
      option.addEventListener('click', () => {
        const theme = option.dataset.theme;
        this.applyTheme(theme);
        
        themeOptions.forEach(opt => opt.classList.remove('active'));
        option.classList.add('active');
      });
    });
    
    // Load saved theme
    const savedTheme = localStorage.getItem('theme') || 'dark';
    this.applyTheme(savedTheme);
  }

  applyTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);
  }

  setupSettingsTabs() {
    const tabs = document.querySelectorAll('.settings-tab');
    
    tabs.forEach(tab => {
      tab.addEventListener('click', () => {
        const tabName = tab.dataset.tab;
        
        tabs.forEach(t => t.classList.remove('active'));
        tab.classList.add('active');
        
        document.querySelectorAll('.settings-tab-content').forEach(content => {
          content.classList.remove('active');
        });
        const tabContent = document.getElementById(`tab-${tabName}`);
        if (tabContent) tabContent.classList.add('active');
      });
    });
  }

  setupWorkflowHandlers() {
    // Handle image upload success
    window.addEventListener('imageUploaded', (event) => {
      console.log('Image uploaded:', event.detail);
      
      // Show original image in viewer
      const viewer = document.getElementById('imageViewer');
      if (viewer) {
        viewer.innerHTML = `<img src="${event.detail.image_url}" alt="Uploaded image" style="max-width: 100%; max-height: 70vh; object-fit: contain; border-radius: var(--radius-md);">`;
      }
      
      // Enable segmentation button if model is selected
      if (this.modelSelector && this.modelSelector.getSelectedModel()) {
        const segBtn = document.getElementById('segment-button');
        if (segBtn) segBtn.disabled = false;
      }
      
      // Enable GPT boundaries button
      const gptBtn = document.getElementById('gpt-boundary-button');
      if (gptBtn) gptBtn.disabled = false;
    });
    
    // Handle model selection
    window.addEventListener('modelSelected', (event) => {
      console.log('Model selected:', event.detail.modelName);
      
      // Enable segmentation button if image is uploaded
      if (this.imageUploader && this.imageUploader.getImageId()) {
        const segBtn = document.getElementById('segment-button');
        if (segBtn) segBtn.disabled = false;
      }
    });
    
    // Handle segmentation completion
    window.addEventListener('segmentationComplete', async (event) => {
      console.log('Segmentation complete:', event.detail);
      
      const result = event.detail;
      const imageData = this.imageUploader ? this.imageUploader.getUploadedImageData() : null;
      
      if (!imageData) {
        console.error('No image data available');
        return;
      }
      
      // Update hidden panels for compatibility with existing components
      const maskPanel = document.getElementById('mask-panel');
      const overlayPanel = document.getElementById('overlay-panel');
      
      // Display mask in hidden panel
      if (maskPanel) {
        maskPanel.innerHTML = `<img src="${result.maskUrl}" alt="Segmentation mask" style="max-width: 100%; max-height: 500px; object-fit: contain;">`;
      }
      
      // Generate overlay
      if (overlayPanel && imageData.image_url) {
        try {
          const canvas = await this.createOverlay(imageData.image_url, result.maskUrl);
          overlayPanel.innerHTML = '';
          canvas.style.maxWidth = '100%';
          canvas.style.maxHeight = '500px';
          canvas.style.objectFit = 'contain';
          overlayPanel.appendChild(canvas);
        } catch (error) {
          console.error('Error creating overlay:', error);
        }
      }
      
      // Update the current view
      this.updateImageViewer();
      
      // Enable boundary detection
      const boundaryBtn = document.getElementById('gpt-boundary-button');
      if (boundaryBtn) boundaryBtn.disabled = false;
      
      // Update dashboard stats
      this.updateDashboardStats();
    });
    
    // Handle boundary detection
    window.addEventListener('boundariesDetected', (event) => {
      console.log('Boundaries detected:', event.detail);
      
      // Show detection results
      const resultsDiv = document.getElementById('detection-results');
      if (resultsDiv) {
        resultsDiv.style.display = 'block';
        const buildingCountEl = document.getElementById('buildingCount');
        if (buildingCountEl) buildingCountEl.textContent = event.detail.totalBuildings || 0;
        const avgConfEl = document.getElementById('avgConfidence');
        if (avgConfEl) avgConfEl.textContent = '94%';
        const procTimeEl = document.getElementById('procTime');
        if (procTimeEl) procTimeEl.textContent = '1.4s';
      }
      
      // Update dashboard
      this.updateDashboardStats();
    });
    
    // Handle GPT boundary detection completion
    window.addEventListener('gptDetectionComplete', (event) => {
      console.log('GPT Detection complete:', event.detail);
      
      // Show the GPT panel wrapper
      const gptPanelWrapper = document.getElementById('gpt-panel-wrapper');
      if (gptPanelWrapper) {
        gptPanelWrapper.style.display = 'block';
      }
      
      // Show detection results
      const resultsDiv = document.getElementById('detection-results');
      if (resultsDiv) {
        resultsDiv.style.display = 'block';
        const buildingCountEl = document.getElementById('buildingCount');
        if (buildingCountEl) buildingCountEl.textContent = event.detail.count || 0;
        const avgConfEl = document.getElementById('avgConfidence');
        if (avgConfEl) avgConfEl.textContent = '94%';
        const procTimeEl = document.getElementById('procTime');
        if (procTimeEl) procTimeEl.textContent = '1.4s';
      }
      
      // Track in dashboard
      if (this.dashboard) {
        this.dashboard.recordDetection(event.detail.imageName, event.detail.count, event.detail.itemId);
        this.updateDashboardStats();
      }
    });
    
    window.addEventListener('fileSaved', (event) => {
      if (this.dashboard) {
        this.dashboard.recordSave(event.detail.filename);
        this.updateDashboardStats();
      }
    });
  }
  
  /**
   * Create overlay by combining image and mask
   */
  async createOverlay(imageUrl, maskUrl) {
    // Load both images
    const [originalImg, maskImg] = await Promise.all([
      this.loadImage(imageUrl),
      this.loadImage(maskUrl)
    ]);
    
    // Create canvas with same dimensions as original image
    const canvas = document.createElement('canvas');
    canvas.width = originalImg.width;
    canvas.height = originalImg.height;
    
    const ctx = canvas.getContext('2d');
    
    // Draw original image
    ctx.drawImage(originalImg, 0, 0);
    
    // Create temporary canvas for mask processing
    const maskCanvas = document.createElement('canvas');
    maskCanvas.width = maskImg.width;
    maskCanvas.height = maskImg.height;
    const maskCtx = maskCanvas.getContext('2d');
    maskCtx.drawImage(maskImg, 0, 0);
    
    // Get mask pixel data
    const maskImageData = maskCtx.getImageData(0, 0, maskImg.width, maskImg.height);
    const maskData = maskImageData.data;
    
    // Create overlay image data
    const overlayCanvas = document.createElement('canvas');
    overlayCanvas.width = originalImg.width;
    overlayCanvas.height = originalImg.height;
    const overlayCtx = overlayCanvas.getContext('2d');
    const overlayImageData = overlayCtx.createImageData(originalImg.width, originalImg.height);
    const overlayData = overlayImageData.data;
    
    // Apply red color to building pixels (white in mask)
    const scaleX = maskImg.width / originalImg.width;
    const scaleY = maskImg.height / originalImg.height;
    
    for (let y = 0; y < originalImg.height; y++) {
      for (let x = 0; x < originalImg.width; x++) {
        const maskX = Math.floor(x * scaleX);
        const maskY = Math.floor(y * scaleY);
        const maskIdx = (maskY * maskImg.width + maskX) * 4;
        const overlayIdx = (y * originalImg.width + x) * 4;
        
        const maskValue = maskData[maskIdx]; // R channel (grayscale)
        
        if (maskValue > 128) { // Building pixel (white in mask)
          overlayData[overlayIdx] = 255;     // R
          overlayData[overlayIdx + 1] = 0;   // G
          overlayData[overlayIdx + 2] = 0;   // B
          overlayData[overlayIdx + 3] = 128; // A (50% transparency)
        } else { // Background pixel
          overlayData[overlayIdx] = 0;
          overlayData[overlayIdx + 1] = 0;
          overlayData[overlayIdx + 2] = 0;
          overlayData[overlayIdx + 3] = 0; // Fully transparent
        }
      }
    }
    
    // Draw overlay on top of original image
    overlayCtx.putImageData(overlayImageData, 0, 0);
    ctx.drawImage(overlayCanvas, 0, 0);
    
    return canvas;
  }
  
  /**
   * Load an image from URL
   */
  loadImage(url) {
    return new Promise((resolve, reject) => {
      const img = new Image();
      img.crossOrigin = 'anonymous'; // Enable CORS
      img.onload = () => resolve(img);
      img.onerror = () => reject(new Error(`Failed to load image: ${url}`));
      img.src = url;
    });
  }

  setupSignOut() {
    const signOutBtn = document.getElementById('signOutBtn');
    if (signOutBtn) {
      signOutBtn.addEventListener('click', () => {
        sessionStorage.clear();
        window.location.href = '/login.html';
      });
    }
  }

  async loadDashboardStats() {
    if (!this.dashboard) return;
    
    const stats = this.dashboard.getStats();
    
    const statTotalImagesEl = document.getElementById('statTotalImages');
    const statActiveBatchEl = document.getElementById('statActiveBatch');
    const statBuildingsEl = document.getElementById('statBuildings');
    const statExportsEl = document.getElementById('statExports');
    
    if (statTotalImagesEl) statTotalImagesEl.textContent = stats.totalImages.toLocaleString();
    if (statActiveBatchEl) statActiveBatchEl.textContent = stats.activeBatches;
    if (statBuildingsEl) statBuildingsEl.textContent = stats.totalBuildings.toLocaleString();
    if (statExportsEl) statExportsEl.textContent = stats.totalExports;
  }

  updateDashboardStats() {
    if (this.currentPage === 'dashboard') {
      this.loadDashboardStats();
    }
  }
  
  loadRecentJobs() {
    const jobsList = document.getElementById('recentJobsList');
    if (!jobsList) return;
    
    jobsList.innerHTML = `
      <div style="padding: 1rem; text-align: center; color: var(--text-tertiary); font-size: 0.875rem;">
        No recent jobs yet. Start processing to see activity here.
      </div>
    `;
  }
}

// Initialize app when DOM is ready
console.log('=== INDEX.JS LOADED ===');
console.log('Document ready state:', document.readyState);

window.addEventListener('error', (event) => {
  console.error('=== GLOBAL ERROR ===');
  console.error('Message:', event.message);
  console.error('Filename:', event.filename);
  console.error('Line:', event.lineno, 'Column:', event.colno);
  console.error('Error object:', event.error);
});

if (document.readyState === 'loading') {
  console.log('Waiting for DOMContentLoaded...');
  document.addEventListener('DOMContentLoaded', () => {
    console.log('DOMContentLoaded fired, creating BhumiAIApp...');
    try {
      const app = new BhumiAIApp();
      console.log('BhumiAIApp created successfully:', app);
    } catch (error) {
      console.error('ERROR creating BhumiAIApp:', error);
      alert('Failed to initialize app: ' + error.message);
    }
  });
} else {
  console.log('DOM already loaded, creating BhumiAIApp immediately...');
  try {
    const app = new BhumiAIApp();
    console.log('BhumiAIApp created successfully:', app);
  } catch (error) {
    console.error('ERROR creating BhumiAIApp:', error);
    alert('Failed to initialize app: ' + error.message);
  }
}

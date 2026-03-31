/**
 * GPTBoundaryDetector
 * Features:
 *   - Static overlay view with Save button (JSON / PNG / JPEG)
 *     Output filename: {original_name}_output.{ext}
 *   - Edit mode: drag vertices, draw new polygons, delete polygons
 */
export class GPTBoundaryDetector {
  constructor(imageUploader, modelSelector) {
    this.imageUploader = imageUploader;
    this.modelSelector = modelSelector;

    this._polygons     = [];
    this._overlayB64   = null;
    this._imageUrl     = null;
    this._editMode     = false;
    this._drawMode     = false;
    this._drawPoints   = [];
    this._dragState    = null;
    this._svg          = null;
    this._imgW         = 0;
    this._imgH         = 0;
    this._selectedPoly = null;

    this._gptPanel     = document.getElementById('gpt-panel');
    this._gptPanelWrap = document.getElementById('gpt-panel-wrapper');
    this._gptStatus    = document.getElementById('gpt-status');
    this._gptInfoBar   = document.getElementById('gpt-info-bar');
    this._editBar      = document.getElementById('gpt-edit-bar');
    this._editBtn      = document.getElementById('gpt-edit-button');
    this._doneBtn      = document.getElementById('gpt-done-button');
    this._gptBtn       = document.getElementById('gpt-boundary-button');

    this._setupButtonListeners();
  }

  _setupButtonListeners() {
    if (this._gptBtn)  this._gptBtn.addEventListener('click',  () => this._runDetection());
    if (this._editBtn) this._editBtn.addEventListener('click', () => this._enterEditMode());
    if (this._doneBtn) this._doneBtn.addEventListener('click', () => this._exitEditMode());
  }

  // ── Filename helper ────────────────────────────────────────────────────────

  _baseName() {
    const name = (this.imageUploader && this.imageUploader.getOriginalFilename)
      ? this.imageUploader.getOriginalFilename()
      : 'output';
    return name + '_output';
  }

  // ── Detection ──────────────────────────────────────────────────────────────

  async _runDetection() {
    const imageId = this.imageUploader ? this.imageUploader.getImageId() : null;
    const model   = this.modelSelector  ? this.modelSelector.getSelectedModel() : null;
    if (!imageId || !model) {
      this._setStatus('Please upload an image and select a model first.', 'error');
      return;
    }
    this._setStatus('Detecting boundaries...', 'info');
    if (this._gptBtn) this._gptBtn.disabled = true;
    try {
      const resp = await fetch('http://localhost:8000/api/gpt-boundaries', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ image_id: imageId, model })
      });
      if (!resp.ok) {
        const err = await resp.json().catch(() => ({ detail: resp.statusText }));
        throw new Error(err.detail || 'Detection failed');
      }
      const data = await resp.json();
      this._overlayB64 = data.gpt_overlay_b64;
      this._polygons   = data.polygons || [];
      this._imageUrl   = data.image_url ? 'http://localhost:8000' + data.image_url : null;
      this._setStatus('Found ' + data.building_count + ' building(s) in ' + data.processing_time_s + 's', 'success');
      this._showStaticOverlay();
    } catch (e) {
      this._setStatus('Error: ' + e.message, 'error');
    } finally {
      if (this._gptBtn) this._gptBtn.disabled = false;
    }
  }

  // ── Static overlay ─────────────────────────────────────────────────────────

  _showStaticOverlay() {
    if (!this._gptPanel || !this._overlayB64) return;
    this._editMode   = false;
    this._drawMode   = false;
    this._drawPoints = [];

    if (this._gptPanelWrap) this._gptPanelWrap.style.display = '';
    this._gptPanel.innerHTML = '';

    const img = document.createElement('img');
    img.src = 'data:image/png;base64,' + this._overlayB64;
    img.alt = 'GPT boundary overlay';
    img.style.cssText = 'max-width:100%;max-height:500px;object-fit:contain;display:block;';
    this._gptPanel.appendChild(img);

    // Save bar
    const saveBar = document.createElement('div');
    saveBar.style.cssText = 'display:flex;gap:8px;margin-top:8px;align-items:center;flex-wrap:wrap;';
    const saveLabel = document.createElement('span');
    saveLabel.textContent = 'Save as:';
    saveLabel.style.cssText = 'font-size:13px;color:#444;font-weight:600;';
    saveBar.appendChild(saveLabel);
    saveBar.appendChild(this._makeBtn('JSON', '#27ae60', () => this._saveJSON()));
    saveBar.appendChild(this._makeBtn('PNG',  '#2196F3', () => this._saveImage('png')));
    saveBar.appendChild(this._makeBtn('JPEG', '#9b59b6', () => this._saveImage('jpeg')));
    this._gptPanel.appendChild(saveBar);

    if (this._editBar)  this._editBar.style.display  = '';
    if (this._editBtn)  this._editBtn.style.display  = '';
    if (this._doneBtn)  this._doneBtn.style.display  = 'none';
    if (this._gptInfoBar) {
      this._gptInfoBar.textContent = this._polygons.length + ' building(s) detected';
      this._gptInfoBar.style.display = '';
    }
  }

  _makeBtn(label, bg, onClick) {
    const btn = document.createElement('button');
    btn.textContent = label;
    btn.style.cssText = 'padding:4px 12px;background:' + bg + ';color:#fff;border:none;border-radius:4px;cursor:pointer;font-size:13px;';
    btn.addEventListener('click', onClick);
    return btn;
  }

  // ── Save: JSON ─────────────────────────────────────────────────────────────

  _saveJSON() {
    const payload = {
      building_count: this._polygons.length,
      polygons: this._polygons.map((poly, i) => ({
        id: i,
        coordinates: poly,
        type: 'rotated_rect'
      }))
    };
    const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' });
    this._download(blob, this._baseName() + '.json');
  }

  // ── Save: PNG / JPEG ───────────────────────────────────────────────────────

  _saveImage(format) {
    const src = this._imageUrl || ('data:image/png;base64,' + this._overlayB64);
    const bgImg = new Image();
    bgImg.crossOrigin = 'anonymous';
    bgImg.onload = () => {
      const canvas = document.createElement('canvas');
      canvas.width  = bgImg.naturalWidth;
      canvas.height = bgImg.naturalHeight;
      const ctx = canvas.getContext('2d');
      ctx.drawImage(bgImg, 0, 0);
      this._polygons.forEach(poly => {
        if (!poly || poly.length < 3) return;
        ctx.beginPath();
        ctx.moveTo(poly[0][0], poly[0][1]);
        for (let i = 1; i < poly.length; i++) ctx.lineTo(poly[i][0], poly[i][1]);
        ctx.closePath();
        ctx.strokeStyle = 'red';
        ctx.lineWidth   = 1.5;
        ctx.stroke();
        ctx.fillStyle = 'rgba(255,0,0,0.12)';
        ctx.fill();
      });
      const mimeType = format === 'jpeg' ? 'image/jpeg' : 'image/png';
      const quality  = format === 'jpeg' ? 0.92 : undefined;
      canvas.toBlob(blob => {
        this._download(blob, this._baseName() + '.' + format);
      }, mimeType, quality);
    };
    bgImg.onerror = () => {
      const byteStr = atob(this._overlayB64);
      const arr = new Uint8Array(byteStr.length);
      for (let i = 0; i < byteStr.length; i++) arr[i] = byteStr.charCodeAt(i);
      this._download(new Blob([arr], { type: 'image/png' }), this._baseName() + '.png');
    };
    bgImg.src = src;
  }

  _download(blob, filename) {
    const url = URL.createObjectURL(blob);
    const a   = document.createElement('a');
    a.href = url; a.download = filename; a.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }

  // ── Enter edit mode ────────────────────────────────────────────────────────

  _enterEditMode() {
    if (!this._gptPanel || !this._overlayB64) return;
    this._editMode = true;
    const refImg = new Image();
    refImg.onload = () => this._buildSVGEditor(refImg.naturalWidth, refImg.naturalHeight);
    refImg.src = 'data:image/png;base64,' + this._overlayB64;
  }

  // ── Build SVG editor ───────────────────────────────────────────────────────

  _buildSVGEditor(imgW, imgH) {
    if (!this._gptPanel) return;
    this._imgW = imgW; this._imgH = imgH;
    this._gptPanel.innerHTML = '';

    const toolbar = document.createElement('div');
    toolbar.style.cssText = 'display:flex;gap:8px;margin-bottom:6px;align-items:center;flex-wrap:wrap;';

    this._drawBtn = document.createElement('button');
    this._drawBtn.textContent = 'Draw Polygon';
    this._drawBtn.style.cssText = 'padding:4px 10px;background:#2196F3;color:#fff;border:none;border-radius:4px;cursor:pointer;';
    this._drawBtn.addEventListener('click', () => this._toggleDrawMode());

    this._cancelDrawBtn = document.createElement('button');
    this._cancelDrawBtn.textContent = 'Cancel Draw';
    this._cancelDrawBtn.style.cssText = 'padding:4px 10px;background:#e74c3c;color:#fff;border:none;border-radius:4px;cursor:pointer;display:none;';
    this._cancelDrawBtn.addEventListener('click', () => this._cancelDraw());

    const hint = document.createElement('span');
    hint.style.cssText = 'font-size:12px;color:#666;';
    hint.textContent = 'Click polygon to select, drag handles to move';
    this._hint = hint;

    toolbar.appendChild(this._drawBtn);
    toolbar.appendChild(this._cancelDrawBtn);
    toolbar.appendChild(hint);

    const container = document.createElement('div');
    container.style.cssText = 'position:relative;display:inline-block;max-width:100%;';

    const bgImg = document.createElement('img');
    bgImg.src = this._imageUrl || ('data:image/png;base64,' + this._overlayB64);
    bgImg.alt = 'Original image';
    bgImg.style.cssText = 'display:block;max-width:100%;max-height:500px;object-fit:contain;';

    const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    svg.style.cssText = 'position:absolute;top:0;left:0;width:100%;height:100%;overflow:visible;';
    svg.setAttribute('viewBox', '0 0 ' + imgW + ' ' + imgH);
    svg.setAttribute('preserveAspectRatio', 'xMidYMid meet');
    this._svg = svg;

    this._polygons.forEach((poly, polyIdx) => this._renderPoly(svg, poly, polyIdx));
    svg.addEventListener('click',    (e) => this._onSVGClick(e));
    svg.addEventListener('dblclick', (e) => this._onSVGDblClick(e));

    container.appendChild(bgImg);
    container.appendChild(svg);
    this._gptPanel.appendChild(toolbar);
    this._gptPanel.appendChild(container);

    if (this._editBtn) this._editBtn.style.display = 'none';
    if (this._doneBtn) this._doneBtn.style.display = '';
  }

  // ── Render one polygon ─────────────────────────────────────────────────────

  _renderPoly(svg, poly, polyIdx) {
    if (!poly || poly.length < 3) return;
    const g = document.createElementNS('http://www.w3.org/2000/svg', 'g');
    g.dataset.polyIdx = polyIdx;

    const polygon = document.createElementNS('http://www.w3.org/2000/svg', 'polygon');
    polygon.setAttribute('points', poly.map(p => p[0]+','+p[1]).join(' '));
    polygon.setAttribute('fill', 'rgba(255,0,0,0.15)');
    polygon.setAttribute('stroke', 'red');
    polygon.setAttribute('stroke-width', '1.5');
    polygon.style.cursor = 'pointer';
    polygon.addEventListener('click', (e) => { e.stopPropagation(); this._selectPoly(polyIdx); });
    g.appendChild(polygon);

    const cx = poly.reduce((s,p)=>s+p[0],0)/poly.length;
    const cy = poly.reduce((s,p)=>s+p[1],0)/poly.length;
    const fo = document.createElementNS('http://www.w3.org/2000/svg', 'foreignObject');
    fo.setAttribute('x', cx-14); fo.setAttribute('y', cy-10);
    fo.setAttribute('width', 28); fo.setAttribute('height', 20);
    fo.style.display = 'none'; fo.dataset.deleteBtn = polyIdx;
    const delBtn = document.createElement('button');
    delBtn.textContent = 'x'; delBtn.title = 'Delete polygon';
    delBtn.style.cssText = 'width:28px;height:20px;background:#e74c3c;color:#fff;border:none;border-radius:3px;cursor:pointer;font-size:11px;padding:0;line-height:1;';
    delBtn.addEventListener('click', (e) => { e.stopPropagation(); this._deletePoly(polyIdx); });
    fo.appendChild(delBtn);
    g.appendChild(fo);

    poly.forEach((pt, ptIdx) => {
      const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
      circle.setAttribute('cx', pt[0]); circle.setAttribute('cy', pt[1]);
      circle.setAttribute('r', '5');
      circle.setAttribute('fill', '#2196F3');
      circle.setAttribute('stroke', 'white'); circle.setAttribute('stroke-width', '1.5');
      circle.style.cursor = 'grab';
      circle.dataset.polyIdx = polyIdx; circle.dataset.ptIdx = ptIdx;
      circle.addEventListener('mousedown', (e) => { e.stopPropagation(); this._onHandleMouseDown(e, polyIdx, ptIdx); });
      g.appendChild(circle);
    });

    svg.appendChild(g);
  }

  _selectPoly(polyIdx) {
    if (!this._svg) return;
    this._svg.querySelectorAll('foreignObject[data-delete-btn]').forEach(fo => fo.style.display = 'none');
    if (this._selectedPoly === polyIdx) { this._selectedPoly = null; return; }
    this._selectedPoly = polyIdx;
    const fo = this._svg.querySelector('foreignObject[data-delete-btn="' + polyIdx + '"]');
    if (fo) fo.style.display = '';
  }

  _deletePoly(polyIdx) {
    this._polygons.splice(polyIdx, 1);
    this._selectedPoly = null;
    this._buildSVGEditor(this._imgW, this._imgH);
    if (this._gptInfoBar) this._gptInfoBar.textContent = this._polygons.length + ' building(s)';
  }

  // ── Draw mode ──────────────────────────────────────────────────────────────

  _toggleDrawMode() {
    this._drawMode = !this._drawMode;
    this._drawPoints = [];
    if (this._drawMode) {
      this._drawBtn.textContent = 'Drawing... (dbl-click to finish)';
      this._drawBtn.style.background = '#ff9800';
      this._cancelDrawBtn.style.display = '';
      if (this._hint) this._hint.textContent = 'Click to add vertices, double-click to close';
      if (this._svg) this._svg.style.cursor = 'crosshair';
    } else {
      this._resetDrawUI();
    }
  }

  _resetDrawUI() {
    this._drawMode = false; this._drawPoints = [];
    if (this._drawBtn) { this._drawBtn.textContent = 'Draw Polygon'; this._drawBtn.style.background = '#2196F3'; }
    if (this._cancelDrawBtn) this._cancelDrawBtn.style.display = 'none';
    if (this._hint) this._hint.textContent = 'Click polygon to select, drag handles to move';
    if (this._svg) {
      this._svg.style.cursor = '';
      const prev = this._svg.querySelector('#draw-preview');
      if (prev) prev.remove();
    }
  }

  _cancelDraw() { this._resetDrawUI(); }

  _svgCoords(e) {
    const rect = this._svg.getBoundingClientRect();
    return [
      Math.round((e.clientX - rect.left) * (this._imgW / rect.width)),
      Math.round((e.clientY - rect.top)  * (this._imgH / rect.height))
    ];
  }

  _onSVGClick(e) {
    if (!this._drawMode) return;
    if (e.detail >= 2) return;
    this._drawPoints.push(this._svgCoords(e));
    this._updateDrawPreview();
  }

  _onSVGDblClick(e) {
    if (!this._drawMode) return;
    e.preventDefault();
    if (this._drawPoints.length > 0) this._drawPoints.pop();
    if (this._drawPoints.length >= 3) {
      this._polygons.push([...this._drawPoints]);
      this._resetDrawUI();
      this._buildSVGEditor(this._imgW, this._imgH);
      if (this._gptInfoBar) this._gptInfoBar.textContent = this._polygons.length + ' building(s)';
    } else {
      this._setStatus('Need at least 3 points to close a polygon.', 'error');
      this._resetDrawUI();
    }
  }

  _updateDrawPreview() {
    if (!this._svg) return;
    let prev = this._svg.querySelector('#draw-preview');
    if (!prev) { prev = document.createElementNS('http://www.w3.org/2000/svg', 'g'); prev.id = 'draw-preview'; this._svg.appendChild(prev); }
    prev.innerHTML = '';
    const pts = this._drawPoints;
    if (pts.length >= 2) {
      const pl = document.createElementNS('http://www.w3.org/2000/svg', 'polyline');
      pl.setAttribute('points', pts.map(p=>p[0]+','+p[1]).join(' '));
      pl.setAttribute('fill', 'none'); pl.setAttribute('stroke', '#ff9800');
      pl.setAttribute('stroke-width', '1.5'); pl.setAttribute('stroke-dasharray', '4 2');
      prev.appendChild(pl);
    }
    pts.forEach(pt => {
      const c = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
      c.setAttribute('cx', pt[0]); c.setAttribute('cy', pt[1]); c.setAttribute('r', '4'); c.setAttribute('fill', '#ff9800');
      prev.appendChild(c);
    });
  }

  // ── Drag handles ───────────────────────────────────────────────────────────

  _onHandleMouseDown(e, polyIdx, ptIdx) {
    e.preventDefault();
    const rect = this._svg.getBoundingClientRect();
    this._dragState = { polyIdx, ptIdx, rect, scaleX: this._imgW / rect.width, scaleY: this._imgH / rect.height };
    const onMove = (ev) => this._onMouseMove(ev);
    const onUp   = () => { this._dragState = null; window.removeEventListener('mousemove', onMove); window.removeEventListener('mouseup', onUp); };
    window.addEventListener('mousemove', onMove);
    window.addEventListener('mouseup', onUp);
  }

  _onMouseMove(e) {
    if (!this._dragState || !this._svg) return;
    const { polyIdx, ptIdx, rect, scaleX, scaleY } = this._dragState;
    const newX = Math.round((e.clientX - rect.left) * scaleX);
    const newY = Math.round((e.clientY - rect.top)  * scaleY);
    this._polygons[polyIdx][ptIdx] = [newX, newY];
    const g = this._svg.querySelector('g[data-poly-idx="' + polyIdx + '"]');
    if (g) {
      const polygon = g.querySelector('polygon');
      if (polygon) polygon.setAttribute('points', this._polygons[polyIdx].map(p=>p[0]+','+p[1]).join(' '));
      g.querySelectorAll('circle[data-pt-idx="' + ptIdx + '"]').forEach(c => { c.setAttribute('cx', newX); c.setAttribute('cy', newY); });
    }
  }

  // ── Exit edit mode ─────────────────────────────────────────────────────────

  _exitEditMode() { this._showStaticOverlay(); }

  // ── Status ─────────────────────────────────────────────────────────────────

  _setStatus(msg, type) {
    if (!this._gptStatus) return;
    this._gptStatus.textContent = msg;
    this._gptStatus.style.color = type === 'error' ? '#e74c3c' : type === 'success' ? '#27ae60' : '#3498db';
  }
}

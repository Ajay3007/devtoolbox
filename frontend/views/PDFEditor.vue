<template>
  <div class="pdf-editor-page">
    <h1>📄 PDF Editor</h1>
    <p class="subtitle">Click any text on the page to edit it. Changes are saved to a new file.</p>

    <!-- ── Upload Zone ── -->
    <div v-if="!pdf" class="upload-zone" @click="$refs.fileInput.click()"
         @dragover.prevent @drop.prevent="onDrop">
      <input ref="fileInput" type="file" accept=".pdf" @change="onFileSelect" hidden />
      <div class="upload-icon">📄</div>
      <p class="upload-text">Drop a PDF here or <strong>click to upload</strong></p>
      <p class="upload-hint">Supported: .pdf</p>
      <div v-if="uploading" class="upload-spinner">⏳ Uploading…</div>
      <p v-if="uploadError" class="upload-error">❌ {{ uploadError }}</p>
    </div>

    <!-- ── Editor Layout ── -->
    <div v-else class="editor-layout">

      <!-- Left: page list -->
      <aside class="page-list">
        <div class="pane-header">
          <span>Pages</span>
          <button class="btn-icon-sm" @click="resetEditor" title="Close">✕</button>
        </div>
        <div v-for="n in pdf.page_count" :key="n"
             class="page-thumb" :class="{ active: currentPage === n - 1, deleted: isDeleted(n - 1) }"
             @click="goToPage(n - 1)">
          <div class="thumb-info">
            <span class="thumb-num">{{ n }}</span>
            <span v-if="editsByPage[n-1]" class="thumb-badge">
              {{ editsByPage[n-1].length }}✏️
            </span>
          </div>
          <button class="btn-icon-sm btn-delete-page" @click.stop="toggleDeletePage(n - 1)" 
                  :title="isDeleted(n - 1) ? 'Restore Page' : 'Delete Page'">
            {{ isDeleted(n - 1) ? '↩️' : '🗑️' }}
          </button>
        </div>
        
        <div class="append-section">
          <input ref="appendFileInput" type="file" accept=".pdf" @change="onAppendFileSelect" hidden />
          <button class="btn btn-append" @click="$refs.appendFileInput.click()" :disabled="appending">
            {{ appending ? '⏳ Appending…' : '📄+ Append PDF' }}
          </button>
        </div>

        <!-- Export Section -->
        <div class="export-section" v-if="pdf">
          <div class="edits-summary" v-if="allEdits.length || deletedPages.length">
            <p>
              <strong>{{ allEdits.length }}</strong> edit(s), 
              <strong>{{ deletedPages.length }}</strong> deleted page(s)
            </p>
            <button class="btn btn-clear" @click="clearAllEdits">🗑 Clear All Edits</button>
          </div>
          
          <div class="output-name-row" style="margin-top:0.75rem">
            <input v-model="outputName" class="output-input" placeholder="output_filename.pdf" />
          </div>
          <button class="btn btn-save" @click="saveAndDownload" :disabled="saving">
            {{ saving ? '⏳ Processing…' : '💾 Save & Download' }}
          </button>
        </div>

        <!-- Metadata Section -->
        <div class="metadata-section" v-if="metadataEdits">
          <div class="pane-subheader" @click="showMetadata = !showMetadata" style="cursor:pointer; margin-top:0;">
            {{ showMetadata ? '▼' : '▶' }} ℹ️ Document Info
          </div>
          <div v-show="showMetadata" class="metadata-form">
            <label class="meta-label">Title</label>
            <input v-model="metadataEdits.title" class="meta-input" />
            
            <label class="meta-label">Author</label>
            <input v-model="metadataEdits.author" class="meta-input" />
            
            <label class="meta-label">Subject</label>
            <input v-model="metadataEdits.subject" class="meta-input" />
            
            <label class="meta-label">Creator</label>
            <input v-model="metadataEdits.creator" class="meta-input" />
          </div>
        </div>

        <!-- Watermark Section -->
        <div class="metadata-section" v-if="pdf">
          <div class="pane-subheader" @click="showWatermark = !showWatermark" style="cursor:pointer; margin-top:0;">
            {{ showWatermark ? '▼' : '▶' }} 💧 Watermark
          </div>
          <div v-show="showWatermark" class="metadata-form">
            <label class="meta-label">Text (e.g. CONFIDENTIAL)</label>
            <input v-model="watermarkConfig.text" class="meta-input" placeholder="No watermark" />
            
            <div style="display:flex; gap:0.5rem; margin-top:0.3rem;">
              <div style="flex:1;">
                <label class="meta-label">Color (RGB)</label>
                <input type="color" v-model="watermarkConfig.hexColor" class="meta-input" style="padding:0; height:30px;" />
              </div>
              <div style="flex:1;">
                <label class="meta-label">Opacity (0.1 - 1)</label>
                <input type="number" v-model.number="watermarkConfig.opacity" class="meta-input" step="0.1" min="0.1" max="1" />
              </div>
            </div>
          </div>
        </div>
      </aside>

      <!-- Center: page canvas -->
      <main class="page-canvas-wrap">
        <div v-if="pageLoading" class="page-loading">⏳ Rendering page…</div>
        <div v-else-if="pageData" class="page-canvas" ref="pageCanvas"
             :style="{ width: pageData.img_width + 'px', height: pageData.img_height + 'px' }">

          <!-- Rendered page image -->
          <img :src="'data:image/png;base64,' + pageData.image"
               :width="pageData.img_width" :height="pageData.img_height"
               class="page-image" draggable="false" />

          <!-- Text-span overlays -->
          <div v-for="span in currentSpans" :key="span.id"
               class="span-overlay"
               :class="{
                 selected: selected && selected.id === span.id,
                 edited: isEdited(span)
               }"
               :style="spanStyle(span)"
               @click="selectSpan(span)"
               :title="span.text">
          </div>
        </div>
        <div v-else class="page-empty">Select a page to view it.</div>

        <!-- Page nav -->
        <div class="page-nav" v-if="pdf">
          <button class="btn-nav" :disabled="currentPage === 0" @click="goToPage(currentPage - 1)">◀</button>
          <span>Page {{ currentPage + 1 }} / {{ pdf.page_count }}</span>
          <button class="btn-nav" :disabled="currentPage === pdf.page_count - 1" @click="goToPage(currentPage + 1)">▶</button>
        </div>
      </main>

      <!-- Right: edit panel -->
      <aside class="edit-panel">
        <div class="pane-header">✏️ Text Editor</div>

        <div v-if="!selected" class="edit-placeholder">
          <p>👆 Click on any text block in the PDF to edit it.</p>
        </div>

        <div v-else class="edit-form">
          <div class="edit-meta">
            <span class="meta-pill">{{ selected.font }}</span>
            <span class="meta-pill">{{ selected.size }}pt</span>
            <span class="meta-pill" v-if="selected.flags & 16">Bold</span>
            <span class="meta-pill italic-pill" v-if="selected.flags & 2">Italic</span>
          </div>

          <label class="edit-label">Original Text</label>
          <div class="original-text">{{ selected.text }}</div>

          <label class="edit-label">New Text</label>
          <textarea v-model="editText" class="edit-textarea"
                    :style="{ fontSize: Math.min(selected.size * 1.1, 18) + 'px' }"
                    rows="4" placeholder="Enter replacement text…" />

          <div class="edit-actions">
            <button class="btn btn-apply" @click="applyEdit('replace')"
                    :disabled="!editText || editText === selected.text">
              ✅ Apply
            </button>
            <button class="btn btn-redact" @click="applyEdit('redact')" title="Blackout text entirely">
              ⬛ Redact
            </button>
            <button class="btn btn-skip" @click="selected = null">Cancel</button>
          </div>

          <p v-if="editApplied" class="applied-msg">{{ editApplied }}</p>
        </div>

        <!-- Edits on this page -->
        <div v-if="pageEdits.length" class="page-edits-list">
          <div class="pane-subheader">Edits on page {{ currentPage + 1 }}</div>
          <div v-for="(edit, i) in pageEdits" :key="i" class="edit-chip">
            <span class="edit-chip-old">{{ truncate(edit.original_text) }}</span>
            <span class="edit-chip-arrow">→</span>
            <span class="edit-chip-new" v-if="edit.action === 'redact'">[REDACTED]</span>
            <span class="edit-chip-new" v-else>{{ truncate(edit.new_text) }}</span>
            <button class="chip-del" @click="removeEdit(edit)" title="Remove">✕</button>
          </div>
        </div>
      </aside>
    </div>

    <!-- Save success -->
    <transition name="toast">
      <div v-if="saveResult" class="toast-success">
        ✅ Saved as <strong>{{ saveResult.filename }}</strong> —
        <button class="toast-dl" @click="downloadResult">⬇ Download</button>
      </div>
    </transition>
  </div>
</template>

<script>
export default {
  name: 'PDFEditor',
  data() {
    return {
      pdf:          null,   // { filepath, filename, page_count, metadata }
      uploading:    false,
      uploadError:  null,
      currentPage:  0,
      pageData:     null,   // { image, img_width, img_height, page_width, page_height, scale }
      pageLoading:  false,
      currentSpans: [],
      selected:     null,   // currently clicked span
      editText:     '',
      editApplied:  '',
      allEdits:     [],     // [{page, bbox, original_text, new_text, font, size, flags, color_rgb, action}]
      deletedPages: [],
      metadataEdits:null,   // { title, author, subject, creator }
      showMetadata: false,
      watermarkConfig: { text: '', hexColor: '#e74c3c', opacity: 0.2 },
      showWatermark: false,
      appending:    false,
      saving:       false,
      saveResult:   null,
      outputName:   '',
    };
  },

  computed: {
    editsByPage() {
      const m = {};
      this.allEdits.forEach(e => {
        m[e.page] = m[e.page] || [];
        m[e.page].push(e);
      });
      return m;
    },
    pageEdits() {
      return this.allEdits.filter(e => e.page === this.currentPage);
    },
  },

  methods: {
    // ── Upload ──────────────────────────────────────────────────────────
    onFileSelect(e) { this.upload(e.target.files[0]); },
    onDrop(e)       { this.upload(e.dataTransfer.files[0]); },

    async upload(file) {
      if (!file || !file.name.toLowerCase().endsWith('.pdf')) {
        this.uploadError = 'Please select a PDF file.';
        return;
      }
      this.uploading   = true;
      this.uploadError = null;
      const form = new FormData();
      form.append('file', file);
      try {
        const res = await this.$axios.post('/pdf/upload', form);
        if (res.data.success) {
          this.pdf = res.data.data;
          this.metadataEdits = { ...this.pdf.metadata };
          this.outputName = this.pdf.filename.replace('.pdf', '_edited.pdf');
          await this.goToPage(0);
        } else {
          this.uploadError = res.data.message || 'Upload failed';
        }
      } catch (err) {
        this.uploadError = err.response?.data?.message || err.message || 'Upload failed';
      } finally {
        this.uploading = false;
      }
    },

    onAppendFileSelect(e) {
      const file = e.target.files[0];
      if (file) this.appendPdf(file);
      e.target.value = ''; // Reset input
    },

    async appendPdf(file) {
      if (!file || !file.name.toLowerCase().endsWith('.pdf')) {
        alert('Please select a valid PDF file to append.');
        return;
      }
      this.appending = true;
      const form = new FormData();
      form.append('file', file);
      try {
        const res = await this.$axios.post(`/pdf/${this.pdf.filepath}/append`, form);
        if (res.data.success) {
          this.pdf.page_count = res.data.data.page_count;
          alert('PDF appended successfully!');
        } else {
          alert('Append failed: ' + (res.data.message || 'Unknown error'));
        }
      } catch (err) {
        alert('Append error: ' + (err.response?.data?.message || err.message));
      } finally {
        this.appending = false;
      }
    },

    resetEditor() {
      this.pdf = null; this.pageData = null; this.currentSpans = [];
      this.selected = null; this.allEdits = []; this.deletedPages = []; 
      this.metadataEdits = null; this.showMetadata = false;
      this.watermarkConfig = { text: '', hexColor: '#e74c3c', opacity: 0.2 };
      this.showWatermark = false;
      this.saveResult = null;
    },

    // ── Page navigation ─────────────────────────────────────────────────
    async goToPage(n) {
      this.currentPage = n;
      this.selected    = null;
      this.editApplied = '';
      this.pageLoading = true;
      this.currentSpans = [];
      try {
        const [pageRes, textRes] = await Promise.all([
          this.$axios.get(`/pdf/${this.pdf.filepath}/page/${n}`),
          this.$axios.get(`/pdf/${this.pdf.filepath}/text/${n}`),
        ]);
        if (pageRes.data.success) this.pageData = pageRes.data.data;
        if (textRes.data.success) this.currentSpans = textRes.data.data.spans;
      } catch (err) {
        console.error('Page load error', err);
      } finally {
        this.pageLoading = false;
      }
    },

    // ── Span helpers ────────────────────────────────────────────────────
    spanStyle(span) {
      const s = this.pageData?.scale || 1.5;
      return {
        left:   span.bbox[0] * s + 'px',
        top:    span.bbox[1] * s + 'px',
        width:  (span.bbox[2] - span.bbox[0]) * s + 'px',
        height: (span.bbox[3] - span.bbox[1]) * s + 'px',
      };
    },

    isEdited(span) {
      return this.allEdits.some(
        e => e.page === this.currentPage &&
             JSON.stringify(e.bbox) === JSON.stringify(span.bbox)
      );
    },

    selectSpan(span) {
      this.selected    = span;
      this.editApplied = '';
      // Prefill with any already-queued edit for this span
      const existing = this.allEdits.find(
        e => e.page === this.currentPage &&
             JSON.stringify(e.bbox) === JSON.stringify(span.bbox)
      );
      this.editText = existing ? existing.new_text : span.text;
    },

    // ── Edit management ─────────────────────────────────────────────────
    applyEdit(action = 'replace') {
      if (!this.selected) return;
      if (action === 'replace' && !this.editText) return;
      // Remove any previous edit for same bbox on same page
      this.allEdits = this.allEdits.filter(
        e => !(e.page === this.currentPage &&
               JSON.stringify(e.bbox) === JSON.stringify(this.selected.bbox))
      );
      this.allEdits.push({
        page:          this.currentPage,
        action:        action,
        bbox:          this.selected.bbox,
        original_text: this.selected.text,
        new_text:      action === 'redact' ? '' : this.editText,
        font:          this.selected.font,
        size:          this.selected.size,
        flags:         this.selected.flags,
        color_rgb:     this.selected.color_rgb,
      });
      if (action === 'redact') {
        this.editApplied = `✅ Redacted: "${this.truncate(this.selected.text)}"`;
      } else {
        this.editApplied = `✅ Edit queued: "${this.truncate(this.selected.text)}" → "${this.truncate(this.editText)}"`;
      }
      this.selected    = null;
    },

    removeEdit(edit) {
      this.allEdits = this.allEdits.filter(e => e !== edit);
    },

    clearAllEdits() {
      this.allEdits = [];
      this.deletedPages = [];
      this.watermarkConfig.text = '';
      if (this.pdf && this.pdf.metadata) {
        this.metadataEdits = { ...this.pdf.metadata };
      }
    },

    isDeleted(pageIndex) {
      return this.deletedPages.includes(pageIndex);
    },

    toggleDeletePage(pageIndex) {
      if (this.isDeleted(pageIndex)) {
        this.deletedPages = this.deletedPages.filter(p => p !== pageIndex);
      } else {
        this.deletedPages.push(pageIndex);
      }
    },

    // ── Save & Download ──────────────────────────────────────────────────
    async saveAndDownload() {
      const hasMetadataChanges = JSON.stringify(this.metadataEdits) !== JSON.stringify(this.pdf.metadata);
      const hasWatermark = !!this.watermarkConfig.text.trim();
      
      this.saving = true;
      this.saveResult = null;
      
      // Convert hex to rgb
      const hex = this.watermarkConfig.hexColor.replace('#', '');
      const r = parseInt(hex.substring(0, 2), 16) / 255;
      const g = parseInt(hex.substring(2, 4), 16) / 255;
      const b = parseInt(hex.substring(4, 6), 16) / 255;

      const payloadWatermark = hasWatermark ? {
        text: this.watermarkConfig.text,
        opacity: this.watermarkConfig.opacity,
        color_rgb: [r, g, b]
      } : null;

      try {
        const res = await this.$axios.post(`/pdf/${this.pdf.filepath}/save`, {
          edits:         this.allEdits,
          deleted_pages: this.deletedPages,
          metadata:      hasMetadataChanges ? this.metadataEdits : null,
          watermark:     payloadWatermark,
          output_name:   this.outputName || null,
        });
        if (res.data.success) {
          this.saveResult = res.data.data;
          this.allEdits   = [];
          this.deletedPages = [];
          setTimeout(() => { this.saveResult = null; }, 10000);
        } else {
          alert('Save failed: ' + (res.data.message || 'Unknown error'));
        }
      } catch (err) {
        alert('Save error: ' + (err.response?.data?.message || err.message));
      } finally {
        this.saving = false;
      }
    },

    downloadResult() {
      if (!this.saveResult) return;
      window.open(
        `${this.$axios.defaults.baseURL}/pdf/download/${this.saveResult.filename}`,
        '_blank'
      );
    },

    truncate(s, n = 28) {
      return s && s.length > n ? s.slice(0, n) + '…' : s;
    },
  },
};
</script>

<style scoped>
.pdf-editor-page {
  max-width: 1400px;
  margin: 0 auto;
  animation: fadeIn 0.4s ease;
}
@keyframes fadeIn { from{opacity:0;transform:translateY(8px)} to{opacity:1;transform:translateY(0)} }

h1 { font-size: 2rem; color: #333; margin-bottom: .25rem; }
.subtitle { color: #666; margin-bottom: 1.5rem; }

/* Upload */
.upload-zone {
  border: 3px dashed #667eea;
  border-radius: 16px;
  padding: 4rem 2rem;
  text-align: center;
  cursor: pointer;
  background: #f8f9ff;
  transition: all .25s;
}
.upload-zone:hover { background: #f0f4ff; border-color: #764ba2; }
.upload-icon { font-size: 4rem; margin-bottom: 1rem; }
.upload-text { font-size: 1.1rem; font-weight: 600; color: #333; }
.upload-hint { color: #999; font-size: .88rem; margin-top: .4rem; }
.upload-spinner { margin-top: 1rem; color: #667eea; font-weight: 600; }
.upload-error { color: #e74c3c; margin-top: .75rem; font-size: .9rem; }

/* Editor layout */
.editor-layout {
  display: grid;
  grid-template-columns: 160px 1fr 300px;
  gap: 1rem;
  align-items: start;
}

/* Pane headers */
.pane-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 700;
  font-size: .95rem;
  color: #667eea;
  padding: .5rem .75rem;
  background: #f0f4ff;
  border-radius: 8px 8px 0 0;
  border-bottom: 2px solid #c8d0f5;
}
.pane-subheader {
  font-weight: 700;
  font-size: .82rem;
  color: #999;
  text-transform: uppercase;
  letter-spacing: .05em;
  margin: 1rem 0 .5rem;
}

/* Page list */
.page-list {
  background: white;
  border-radius: 10px;
  box-shadow: 0 4px 16px rgba(0,0,0,.08);
  overflow: hidden;
  position: sticky;
  top: 1rem;
}
.page-thumb {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: .55rem .75rem;
  cursor: pointer;
  font-size: .88rem;
  border-bottom: 1px solid #f0f0f0;
  transition: background .15s;
}
.page-thumb:hover { background: #f0f4ff; }
.page-thumb.active { background: #667eea; color: white; font-weight: 700; }
.page-thumb.deleted { opacity: 0.6; background: #ffebee; }
.page-thumb.deleted .thumb-num { text-decoration: line-through; color: #e74c3c; }

.thumb-info { display: flex; align-items: center; gap: .5rem; }
.thumb-num { font-weight: 600; }
.thumb-badge { background: #2ecc71; color: white; border-radius: 10px;
               padding: .1rem .4rem; font-size: .72rem; }
.btn-delete-page { opacity: 0.5; transition: opacity .2s; }
.page-thumb:hover .btn-delete-page { opacity: 1; }

.append-section {
  padding: .5rem;
  background: white;
  border-bottom: 1px solid #f0f0f0;
}

.export-section {
  padding: .75rem;
  background: #f8f9ff;
  border-top: 1px solid #c8d0f5;
  margin-top: auto;
}

.edits-summary {
  margin-bottom: .5rem;
}
.edits-summary p { font-size: .82rem; color: #555; margin-bottom: .5rem; }
.no-edits-hint { padding: .75rem; font-size: .8rem; color: #aaa; text-align: center; }

/* Metadata Section */
.metadata-section {
  padding: .75rem;
  background: white;
  border-top: 1px solid #f0f0f0;
}
.metadata-form {
  margin-top: .5rem;
  display: flex;
  flex-direction: column;
  gap: .4rem;
}
.meta-label { font-size: .75rem; font-weight: 600; color: #667eea; }
.meta-input {
  width: 100%;
  box-sizing: border-box;
  padding: .3rem .5rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: .8rem;
  outline: none;
}
.meta-input:focus { border-color: #667eea; }

/* Page canvas */
.page-canvas-wrap {
  display: block;
  text-align: center;
  overflow-x: auto;
  padding-bottom: 1rem;
}
.page-canvas {
  position: relative;
  display: inline-block;
  text-align: left;
  box-shadow: 0 8px 32px rgba(0,0,0,.18);
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: 1rem;
}
.page-image {
  display: block;
  user-select: none;
}
.span-overlay {
  position: absolute;
  cursor: pointer;
  border: 1.5px solid transparent;
  border-radius: 2px;
  transition: background .15s, border-color .15s;
}
.span-overlay:hover { background: rgba(102,126,234,.12); border-color: #667eea; }
.span-overlay.selected { background: rgba(102,126,234,.25); border-color: #667eea; border-width: 2px; }
.span-overlay.edited { background: rgba(46,204,113,.15); border-color: #2ecc71; }

.page-loading, .page-empty {
  padding: 4rem;
  color: #999;
  font-size: 1.1rem;
  text-align: center;
}
.page-nav {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 1rem;
  font-size: .9rem;
  color: #555;
}

/* Edit panel */
.edit-panel {
  background: white;
  border-radius: 10px;
  box-shadow: 0 4px 16px rgba(0,0,0,.08);
  overflow: hidden;
  position: sticky;
  top: 1rem;
  max-height: 90vh;
  overflow-y: auto;
}
.edit-placeholder { padding: 2rem 1rem; color: #aaa; text-align: center; font-size: .9rem; }
.edit-form { padding: 1rem; }

.edit-meta { display: flex; gap: .4rem; flex-wrap: wrap; margin-bottom: .75rem; }
.meta-pill {
  background: #f0f4ff;
  color: #667eea;
  border: 1px solid #c8d0f5;
  border-radius: 10px;
  padding: .2rem .6rem;
  font-size: .75rem;
  font-weight: 600;
}
.italic-pill { font-style: italic; }

.edit-label { font-size: .8rem; font-weight: 700; color: #667eea; display: block; margin-bottom: .25rem; }
.original-text {
  background: #f8f8f8;
  border: 1px solid #eee;
  border-radius: 6px;
  padding: .5rem .75rem;
  font-size: .9rem;
  color: #555;
  margin-bottom: .75rem;
  white-space: pre-wrap;
  word-break: break-word;
}
.edit-textarea {
  width: 100%;
  box-sizing: border-box;
  padding: .6rem .75rem;
  border: 2px solid #c8d0f5;
  border-radius: 8px;
  font-family: inherit;
  resize: vertical;
  outline: none;
  transition: border-color .2s;
  line-height: 1.5;
}
.edit-textarea:focus { border-color: #667eea; }

.edit-actions { display: flex; gap: .5rem; margin-top: .75rem; }
.applied-msg { color: #2ecc71; font-size: .82rem; margin-top: .5rem; font-weight: 600; }

/* Edit chips */
.edit-chip {
  display: flex;
  align-items: center;
  gap: .35rem;
  background: #f8f9ff;
  border: 1px solid #c8d0f5;
  border-radius: 6px;
  padding: .4rem .6rem;
  font-size: .78rem;
  margin-bottom: .4rem;
}
.edit-chip-old { color: #e74c3c; text-decoration: line-through; flex: 1; word-break: break-all; }
.edit-chip-arrow { color: #999; flex-shrink: 0; }
.edit-chip-new { color: #27ae60; flex: 1; word-break: break-all; }
.chip-del { background: none; border: none; cursor: pointer; color: #e74c3c; font-size: .9rem; padding: .1rem; }

/* Buttons */
.btn {
  padding: .55rem 1.1rem;
  border: none;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  font-size: .88rem;
  transition: all .2s;
}
.btn-apply { background: #667eea; color: white; }
.btn-apply:hover:not(:disabled) { background: #5a6fd8; transform: translateY(-1px); }
.btn-apply:disabled { opacity: .5; cursor: not-allowed; }
.btn-redact { background: #34495e; color: white; }
.btn-redact:hover { background: #2c3e50; transform: translateY(-1px); }
.btn-skip { background: #ecf0f1; color: #555; }
.btn-skip:hover { background: #dde1e5; }
.btn-append { background: #e0e7ff; color: #4f46e5; width: 100%; border: 1px dashed #6366f1; }
.btn-append:hover:not(:disabled) { background: #c7d2fe; }
.btn-save { background: linear-gradient(135deg, #27ae60, #1abc9c); color: white; width: 100%; margin-bottom: .5rem; }
.btn-save:disabled { opacity: .5; cursor: not-allowed; }
.btn-clear { background: #ecf0f1; color: #e74c3c; width: 100%; font-size: .8rem; }
.btn-nav {
  background: #f4f6f8;
  border: 1px solid #ddd;
  border-radius: 6px;
  padding: .3rem .65rem;
  cursor: pointer;
  font-size: 1rem;
  transition: background .15s;
}
.btn-nav:disabled { opacity: .35; cursor: not-allowed; }
.btn-icon-sm { background: none; border: none; cursor: pointer; color: #999; font-size: 1rem; }

.output-name-row { margin-bottom: .5rem; }
.output-input {
  width: 100%;
  box-sizing: border-box;
  padding: .4rem .6rem;
  border: 1px solid #c8d0f5;
  border-radius: 6px;
  font-size: .8rem;
  outline: none;
}
.output-input:focus { border-color: #667eea; }

/* Toast */
.toast-success {
  position: fixed;
  bottom: 2rem; right: 2rem;
  background: #2ecc71;
  color: white;
  padding: .9rem 1.4rem;
  border-radius: 10px;
  font-weight: 600;
  box-shadow: 0 6px 24px rgba(46,204,113,.4);
  z-index: 2000;
  display: flex;
  align-items: center;
  gap: .75rem;
}
.toast-dl {
  background: rgba(255,255,255,.25);
  border: 1px solid rgba(255,255,255,.6);
  color: white;
  padding: .3rem .75rem;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 700;
}
.toast-enter-active, .toast-leave-active { transition: all .3s; }
.toast-enter-from, .toast-leave-to { opacity: 0; transform: translateY(1rem); }

@media (max-width: 900px) {
  .editor-layout { grid-template-columns: 1fr; }
  .page-list, .edit-panel { position: static; max-height: none; }
}
</style>

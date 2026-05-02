<template>
  <div class="pdf-page" @dragover.prevent @drop.prevent="onDrop">
    <!-- Hidden inputs -->
    <input type="file" ref="fileInput" @change="onFileSelect" accept=".pdf" style="display: none" />
    
    <ViewHeader
      :icon="IconPDF"
      title="PDF Editor"
      subtitle="Edit text in place, redact, add watermark, or append pages."
    >
      <template #actions v-if="!pdf">
        <button class="btn btn-primary" @click="$refs.fileInput.click()">
          <IconUpload :size="13"/> Upload PDF
        </button>
      </template>
      <template #actions v-else>
        <button class="btn btn-primary" @click="saveAndDownload" :disabled="saving">
          <IconDownload :size="13" v-if="!saving"/>
          <span v-else style="animation: pulse 1s infinite">●</span> {{ saving ? 'Saving...' : 'Save PDF' }}
        </button>
      </template>
    </ViewHeader>

    <template v-if="!pdf">
      <div style="padding: 28px">
        <div class="drop-zone" @click="$refs.fileInput.click()">
          <IconUpload :size="32" style="color: var(--accent); margin-bottom: 12px" />
          <div style="font-size: 14px; font-weight: 500; margin-bottom: 4px; color: var(--text)">Drop a PDF file here to edit</div>
          <div style="font-size: 12px; color: var(--text-dim)">Or click to browse</div>
          
          <div v-if="uploading" style="margin-top: 14px; color: var(--accent); font-size: 12px">
            Uploading...
          </div>
        </div>
      </div>
    </template>

    <template v-else>
      <div class="file-bar">
        <div style="display: flex; align-items: center; gap: 10px; min-width: 0">
          <IconFiles :size="14" style="color: var(--accent-3)" />
          <span class="mono" style="font-size: 12px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis">{{ pdf.filename }}</span>
          <Tag>page {{ currentPage + 1 }} / {{ pdf.page_count }}</Tag>
        </div>
        <div style="display: flex; gap: 6px">
          <button @click="goToPage(Math.max(0, currentPage - 1))" :disabled="currentPage === 0" class="btn btn-ghost" style="padding: 5px 10px">◀ prev</button>
          <button @click="goToPage(Math.min(pdf.page_count - 1, currentPage + 1))" :disabled="currentPage === pdf.page_count - 1" class="btn btn-ghost" style="padding: 5px 10px">next ▶</button>
          <button @click="resetEditor" class="btn btn-ghost" style="padding: 5px 10px">Close</button>
        </div>
      </div>

      <div class="main-grid">
        <div class="sidebar">
          <Panel title="Actions" :padding="14">
            <div style="display: flex; flex-direction: column; gap: 8px">
              <button @click="showMetadata = true" class="btn btn-ghost" style="justify-content: flex-start"><IconFiles :size="13"/> Edit Metadata</button>
              <button @click="showWatermark = true" class="btn btn-ghost" style="justify-content: flex-start"><IconHex :size="13"/> Add Watermark</button>
              <button @click="toggleDeletePage(currentPage)" class="btn btn-ghost" style="justify-content: flex-start; color: var(--accent-4)" :class="{ 'active': isDeleted(currentPage) }">
                <IconX :size="13"/> {{ isDeleted(currentPage) ? 'Restore Page' : 'Delete Page' }}
              </button>
            </div>
          </Panel>

          <Panel title="Edits" :subtitle="`${allEdits.length} total edits`" :padding="14" style="flex: 1">
            <div v-if="allEdits.length === 0" style="color: var(--text-mute); font-size: 12px; text-align: center; padding: 20px 0">
              No edits applied yet.
            </div>
            <div v-else style="display: flex; flex-direction: column; gap: 8px">
              <div v-for="(edit, i) in allEdits" :key="i" class="edit-item">
                <div class="mono" style="font-size: 10px; color: var(--text-mute); margin-bottom: 2px">Page {{ edit.page + 1 }} - {{ edit.action }}</div>
                <div style="font-size: 12px; color: var(--text)">{{ truncate(edit.new_text || edit.original_text) }}</div>
                <button @click="removeEdit(edit)" class="btn-icon" style="position: absolute; right: 4px; top: 4px"><IconX :size="11"/></button>
              </div>
              <button @click="clearAllEdits" class="btn btn-ghost" style="width: 100%; margin-top: 8px; font-size: 11px">Clear all</button>
            </div>
          </Panel>
        </div>

        <div class="pdf-viewer-area">
          <div v-if="pageLoading" style="position: absolute; inset: 0; display: flex; align-items: center; justify-content: center; background: var(--bg); z-index: 10">
            <div style="color: var(--accent); animation: pulse 1s infinite">Loading page...</div>
          </div>

          <!-- Scanned page banner -->
          <div v-if="isScanned && !pageLoading" class="scanned-banner">
            <div style="display: flex; align-items: center; gap: 10px; flex-wrap: wrap">
              <span style="font-size: 13px; font-weight: 600">Scanned PDF — no selectable text detected.</span>
              <template v-if="ocrAvailable">
                <span style="font-size: 12px; color: var(--text-dim)">Run OCR to extract and edit text:</span>
                <select v-model="ocrLang" class="mono" style="background: var(--panel-2); border: 1px solid var(--line); border-radius: 4px; padding: 3px 6px; font-size: 11px">
                  <option value="eng">English</option>
                  <option value="eng+hin">English + Hindi</option>
                  <option value="hin">Hindi</option>
                  <option value="eng+deu">English + German</option>
                  <option value="eng+fra">English + French</option>
                </select>
                <button @click="runOCR" :disabled="ocrRunning" class="btn btn-primary" style="padding: 4px 12px; font-size: 12px">
                  {{ ocrRunning ? 'Running OCR...' : 'Run OCR' }}
                </button>
              </template>
              <template v-else>
                <span style="font-size: 12px; color: #e67e22">
                  Tesseract not installed —
                  <code style="background: var(--panel-3); padding: 2px 5px; border-radius: 3px; font-size: 11px">winget install UB-Mannheim.TesseractOCR</code>
                  then restart the server.
                </span>
              </template>
            </div>
            <div v-if="ocrError" style="margin-top: 6px; font-size: 12px; color: #e74c3c">{{ ocrError }}</div>
          </div>

          <div v-if="pageData && !pageLoading" class="pdf-canvas-wrapper"
               :style="{ opacity: isDeleted(currentPage) ? 0.3 : 1, width: pageData.img_width + 'px', maxWidth: '100%' }">
            <img :src="'data:image/png;base64,' + pageData.image" class="pdf-img" />

            <div
              v-for="(span, i) in currentSpans"
              :key="i"
              class="pdf-span"
              :class="{
                'edited': isEdited(span),
                'selected': selected === span,
                'ocr-span': span.ocr
              }"
              :style="spanStyle(span)"
              @click="selectSpan(span)"
            ></div>
          </div>
          <div v-if="isDeleted(currentPage)" class="deleted-overlay">DELETED</div>
        </div>
        
        <div v-if="selected" class="editor-popup">
          <div style="margin-bottom: 8px; font-size: 11px; color: var(--text-dim)">
            Edit text <span v-if="selected.ocr" style="color: var(--accent-5)">(OCR)</span> — detected size: {{ selected.size.toFixed(1) }}pt
          </div>
          <textarea v-model="editText" class="edit-textarea mono" rows="3"></textarea>
          <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-top: 8px">
            <div>
              <div style="font-size: 10px; color: var(--text-mute); margin-bottom: 3px">Font</div>
              <select v-model="editFont" class="edit-select">
                <option v-for="f in FONT_OPTIONS" :key="f.value" :value="f.value">{{ f.label }}</option>
              </select>
            </div>
            <div>
              <div style="font-size: 10px; color: var(--text-mute); margin-bottom: 3px">Size (pt)</div>
              <input v-model.number="editSize" type="number" min="4" max="72" step="0.5" class="edit-select" />
            </div>
          </div>
          <div style="font-size: 10px; color: var(--text-mute); margin-top: 6px; font-style: italic">
            Preview: <span :style="fontPreviewStyle">{{ editText || 'Sample text 123' }}</span>
          </div>
          <div style="display: flex; gap: 8px; margin-top: 8px">
            <button @click="applyEdit('replace')" class="btn btn-primary" style="flex: 1">Replace</button>
            <button @click="applyEdit('redact')" class="btn btn-danger" style="flex: 1">Redact</button>
            <button @click="selected = null" class="btn btn-ghost">Cancel</button>
          </div>
        </div>
      </div>
    </template>

    <div v-if="uploadError" class="error-strip">{{ uploadError }}</div>

    <!-- Preview Modal — shown automatically after save -->
    <div v-if="previewOpen" class="modal-overlay" @click.self="previewOpen = false">
      <div class="preview-modal">
        <div class="preview-header">
          <div style="font-size: 14px; font-weight: 600; color: var(--text)">
            Preview — <span class="mono" style="font-size: 12px">{{ saveResult?.filename }}</span>
          </div>
          <div style="display: flex; align-items: center; gap: 8px">
            <button @click="previewPage = Math.max(0, previewPage - 1)" :disabled="previewPage === 0" class="btn btn-ghost" style="padding: 4px 10px">◀</button>
            <span style="font-size: 12px; color: var(--text-dim)">{{ previewPage + 1 }} / {{ previewTotalPages }}</span>
            <button @click="previewPage = Math.min(previewTotalPages - 1, previewPage + 1)" :disabled="previewPage >= previewTotalPages - 1" class="btn btn-ghost" style="padding: 4px 10px">▶</button>
            <button @click="downloadResult" class="btn btn-primary" style="padding: 5px 14px">
              <IconDownload :size="13"/> Download
            </button>
            <button @click="previewOpen = false" class="btn btn-ghost" style="padding: 4px 10px"><IconX :size="13"/></button>
          </div>
        </div>
        <div class="preview-body">
          <div v-if="previewLoading" style="display:flex;align-items:center;justify-content:center;height:300px;color:var(--accent)">
            Loading preview...
          </div>
          <img v-else-if="previewImage" :src="'data:image/png;base64,' + previewImage" style="max-width:100%;display:block;margin:0 auto;box-shadow:0 4px 20px rgba(0,0,0,0.4)" />
          <div v-else style="text-align:center;padding:40px;color:var(--text-mute)">Preview unavailable</div>
        </div>
      </div>
    </div>

    <!-- Metadata Modal -->
    <div v-if="showMetadata && metadataEdits" class="modal-overlay" @click.self="showMetadata = false">
      <div class="modal">
        <h3 style="margin-top: 0; margin-bottom: 14px; font-size: 16px">Edit Metadata</h3>
        <Field label="Title" v-model="metadataEdits.title" />
        <div style="margin-top: 10px"><Field label="Author" v-model="metadataEdits.author" /></div>
        <div style="margin-top: 10px"><Field label="Subject" v-model="metadataEdits.subject" /></div>
        <div style="margin-top: 10px"><Field label="Creator" v-model="metadataEdits.creator" /></div>
        <div style="display: flex; gap: 8px; margin-top: 18px">
          <button @click="showMetadata = false" class="btn btn-primary" style="flex: 1">Done</button>
        </div>
      </div>
    </div>

    <!-- Watermark Modal -->
    <div v-if="showWatermark" class="modal-overlay" @click.self="showWatermark = false">
      <div class="modal">
        <h3 style="margin-top: 0; margin-bottom: 14px; font-size: 16px">Add Watermark</h3>
        <Field label="Text" v-model="watermarkConfig.text" placeholder="CONFIDENTIAL" />
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-top: 10px">
          <Field label="Color (Hex)" v-model="watermarkConfig.hexColor" />
          <Field label="Opacity (0-1)" v-model.number="watermarkConfig.opacity" type="number" />
        </div>
        <div style="display: flex; gap: 8px; margin-top: 18px">
          <button @click="showWatermark = false" class="btn btn-primary" style="flex: 1">Done</button>
        </div>
      </div>
    </div>
  </div>
</template>
<script>

import ViewHeader from '../components/ViewHeader.vue'
import Panel from '../components/Panel.vue'
import Tag from '../components/Tag.vue'
import Field from '../components/Field.vue'
import { IconPDF, IconUpload, IconFiles, IconDownload, IconHex, IconX } from '../components/icons'

export default {
  components: { ViewHeader, Panel, Tag, Field, IconPDF, IconUpload, IconFiles, IconDownload, IconHex, IconX },
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
      FONT_OPTIONS: [
        { label: 'Courier Bold  — thermal receipts', value: 'cobo' },
        { label: 'Courier Regular',                  value: 'cour' },
        { label: 'Helvetica',                        value: 'helv' },
        { label: 'Helvetica Bold',                   value: 'helv-b' },
        { label: 'Times Roman',                      value: 'tiro' },
        { label: 'Times Bold',                       value: 'tibo' },
      ],
      selected:     null,   // currently clicked span
      editText:     '',
      editFont:     'cobo',
      editSize:     12,
      editApplied:  '',
      previewOpen:        false,
      previewPage:        0,
      previewTotalPages:  1,
      previewImage:       null,
      previewLoading:     false,
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
      isScanned:    false,
      ocrAvailable: false,
      ocrRunning:   false,
      ocrLang:      'eng',
      ocrError:     null,
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
    fontPreviewStyle() {
      const mono = ['cobo', 'cour', 'coit', 'cobi'];
      const serif = ['tiro', 'tibo', 'tiit', 'tibi'];
      const isBold = ['cobo', 'cobi', 'helv-b', 'helv-bi', 'tibo', 'tibi'].includes(this.editFont);
      const isItalic = ['coit', 'cobi', 'helv-o', 'helv-bi', 'tiit', 'tibi'].includes(this.editFont);
      return {
        fontFamily: mono.includes(this.editFont) ? 'Courier New, monospace'
                  : serif.includes(this.editFont) ? 'Georgia, serif'
                  : 'Helvetica, Arial, sans-serif',
        fontWeight: isBold ? 'bold' : 'normal',
        fontStyle:  isItalic ? 'italic' : 'normal',
        fontSize:   '12px',
        color:      'var(--text)',
      };
    },
  },

  watch: {
    previewPage(n) {
      if (this.previewOpen) this.fetchPreviewPage(n);
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
          this.uploadError = res.data.data?.message || res.data.message || 'Upload failed';
        }
      } catch (err) {
        this.uploadError = err.response?.data?.data?.message || err.response?.data?.message || err.message || 'Upload failed';
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
          alert('Append failed: ' + (res.data.data?.message || res.data.message || 'Unknown error'));
        }
      } catch (err) {
        alert('Append error: ' + (err.response?.data?.data?.message || err.response?.data?.message || err.message));
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
      this.isScanned = false; this.ocrAvailable = false;
      this.ocrRunning = false; this.ocrError = null;
      this.previewOpen = false; this.previewImage = null;
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
        if (textRes.data.success) {
          const td = textRes.data.data;
          this.currentSpans = td.spans || [];
          this.isScanned    = td.is_scanned || false;
          this.ocrAvailable = td.ocr_available || false;
          this.ocrError     = null;
        }
      } catch (err) {
        console.error('Page load error', err);
      } finally {
        this.pageLoading = false;
      }
    },

    // ── OCR ─────────────────────────────────────────────────────────────
    async runOCR() {
      this.ocrRunning = true;
      this.ocrError   = null;
      try {
        const res = await this.$axios.post(
          `/pdf/${this.pdf.filepath}/ocr/${this.currentPage}`,
          { lang: this.ocrLang }
        );
        if (res.data.success) {
          this.currentSpans = res.data.data.spans || [];
          this.isScanned    = false;
        } else {
          this.ocrError = res.data.data?.message || res.data.message || 'OCR failed';
        }
      } catch (err) {
        this.ocrError = err.response?.data?.data?.message || err.response?.data?.message || err.message || 'OCR failed';
      } finally {
        this.ocrRunning = false;
      }
    },

    // ── Span helpers ────────────────────────────────────────────────────
    spanStyle(span) {
      // Use percentage-based positioning so spans stay aligned even when
      // the image shrinks via CSS max-width:100%.
      const pw = this.pageData?.page_width  || 1;
      const ph = this.pageData?.page_height || 1;
      return {
        left:   (span.bbox[0] / pw * 100) + '%',
        top:    (span.bbox[1] / ph * 100) + '%',
        width:  ((span.bbox[2] - span.bbox[0]) / pw * 100) + '%',
        height: ((span.bbox[3] - span.bbox[1]) / ph * 100) + '%',
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
      // For OCR spans default to Courier Bold (matches thermal receipt printing).
      // For native PDF text use the extracted font code directly.
      const defaultFont = span.ocr ? 'cobo' : (span.font || 'cobo');
      this.editFont = existing ? existing.font : defaultFont;
      this.editSize = existing ? existing.size : (span.size || 12);
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
        font:          this.editFont,
        size:          this.editSize,
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
          this.saveResult = {
            ...res.data.data,
            page_count: res.data.data.page_count || this.pdf.page_count,
          };
          this.allEdits     = [];
          this.deletedPages = [];
          await this.openPreview();
          setTimeout(() => { this.saveResult = null; }, 30000);
        } else {
          alert('Save failed: ' + (res.data.data?.message || res.data.message || 'Unknown error'));
        }
      } catch (err) {
        alert('Save error: ' + (err.response?.data?.data?.message || err.response?.data?.message || err.message));
      } finally {
        this.saving = false;
      }
    },

    async openPreview() {
      this.previewOpen       = true;
      this.previewPage       = 0;
      this.previewTotalPages = this.saveResult?.page_count || 1;
      await this.fetchPreviewPage(0);
    },

    async fetchPreviewPage(n) {
      this.previewLoading = true;
      this.previewImage   = null;
      try {
        const res = await this.$axios.get(
          `/pdf/${encodeURIComponent(this.saveResult.filename)}/page/${n}`
        );
        if (res.data.success) this.previewImage = res.data.data.image;
      } catch (e) {
        console.error('Preview error', e);
      } finally {
        this.previewLoading = false;
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
.pdf-page {
  display: flex;
  flex-direction: column;
  height: 100%;
}
.drop-zone {
  border: 2px dashed var(--accent);
  border-radius: 8px;
  padding: 40px;
  text-align: center;
  background: color-mix(in oklab, var(--accent) 5%, transparent);
  cursor: pointer;
  transition: all 0.2s;
}
.drop-zone:hover {
  background: color-mix(in oklab, var(--accent) 10%, transparent);
}
.file-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 28px;
  border-top: 1px solid var(--line);
  border-bottom: 1px solid var(--line);
  background: var(--panel);
}
.main-grid {
  flex: 1;
  display: flex;
  min-height: 0;
  position: relative;
}
.sidebar {
  width: 240px;
  min-width: 240px;
  border-right: 1px solid var(--line);
  display: flex;
  flex-direction: column;
  padding: 14px;
  gap: 14px;
  overflow-y: auto;
  background: var(--bg);
}
.pdf-viewer-area {
  flex: 1;
  min-width: 0;
  background: #1d2126;
  padding: 24px;
  display: flex;
  flex-direction: column;
  align-items: center;
  overflow: auto;
  position: relative;
  gap: 16px;
}
.pdf-canvas-wrapper {
  position: relative;
  box-shadow: 0 20px 60px rgba(0,0,0,0.5);
  transition: opacity 0.2s;
  flex-shrink: 0;
}
.pdf-img {
  display: block;
  max-width: 100%;
  height: auto;
}
.pdf-span {
  position: absolute;
  border-bottom: 1px dashed transparent;
  cursor: pointer;
  border-radius: 2px;
}
.pdf-span:hover {
  background: color-mix(in oklab, var(--accent-3) 20%, transparent);
  border-bottom: 1px dashed var(--accent-3);
}
.pdf-span.edited {
  background: color-mix(in oklab, var(--accent) 20%, transparent);
  border-bottom: 1px dashed var(--accent);
}
.pdf-span.selected {
  background: color-mix(in oklab, var(--accent-2) 30%, transparent);
  border: 1px solid var(--accent-2);
}
.pdf-span.ocr-span {
  border-bottom: 1px dashed color-mix(in oklab, var(--accent-5) 60%, transparent);
}
.pdf-span.ocr-span:hover {
  background: color-mix(in oklab, var(--accent-5) 18%, transparent);
  border-bottom: 1px dashed var(--accent-5);
}
.scanned-banner {
  background: color-mix(in oklab, #e67e22 10%, var(--panel));
  border: 1px solid color-mix(in oklab, #e67e22 35%, transparent);
  border-radius: 6px;
  padding: 10px 14px;
  font-size: 12px;
  color: var(--text);
  flex-shrink: 0;
  align-self: stretch;
}
.deleted-overlay {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%) rotate(-45deg);
  font-size: 64px;
  font-weight: 800;
  color: rgba(231, 76, 60, 0.4);
  pointer-events: none;
}
.editor-popup {
  position: absolute;
  bottom: 28px;
  right: 28px;
  width: 320px;
  background: var(--panel);
  border: 1px solid var(--line);
  border-radius: 8px;
  padding: 14px;
  box-shadow: 0 10px 30px rgba(0,0,0,0.4);
  z-index: 100;
}
.edit-textarea {
  width: 100%;
  background: var(--panel-2);
  border: 1px solid var(--line);
  color: var(--text);
  padding: 8px;
  border-radius: 4px;
  font-size: 12px;
  resize: vertical;
  outline: none;
  box-sizing: border-box;
}
.edit-textarea:focus {
  border-color: var(--accent);
}
.edit-select {
  width: 100%;
  background: var(--panel-2);
  border: 1px solid var(--line);
  color: var(--text);
  padding: 5px 7px;
  border-radius: 4px;
  font-size: 11px;
  font-family: inherit;
  outline: none;
}
.edit-select:focus {
  border-color: var(--accent);
}
.edit-item {
  position: relative;
  background: var(--panel-2);
  border: 1px solid var(--line);
  border-radius: 4px;
  padding: 8px 10px;
  padding-right: 24px;
}
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 8px 12px;
  font-size: 12px;
  font-weight: 600;
  border-radius: 5px;
  cursor: pointer;
  border: none;
  font-family: inherit;
}
.btn-primary {
  background: var(--accent);
  color: #0b0d10;
}
.btn-primary:hover {
  filter: brightness(1.1);
}
.btn-danger {
  background: var(--accent-4);
  color: #fff;
}
.btn-ghost {
  background: var(--panel-2);
  color: var(--text);
  border: 1px solid var(--line-2);
}
.btn-ghost:hover:not(:disabled) {
  background: var(--panel-3);
}
.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.btn-icon {
  background: none;
  border: none;
  color: var(--text-mute);
  cursor: pointer;
  padding: 2px;
}
.btn-icon:hover {
  color: var(--text);
}
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}
.modal {
  background: var(--panel);
  border: 1px solid var(--line);
  border-radius: 8px;
  padding: 20px;
  width: 400px;
  max-width: 90vw;
  box-shadow: 0 20px 50px rgba(0,0,0,0.5);
}
.error-strip, .toast-strip {
  position: fixed;
  bottom: 20px;
  left: 50%;
  transform: translateX(-50%);
  padding: 10px 16px;
  border-radius: 5px;
  font-size: 13px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.2);
  z-index: 1000;
}
.error-strip { background: var(--accent-4); color: #fff; }
.toast-strip { background: var(--accent); color: #0b0d10; }
.preview-modal {
  background: var(--panel);
  border: 1px solid var(--line);
  border-radius: 10px;
  width: min(860px, 94vw);
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  box-shadow: 0 24px 60px rgba(0,0,0,0.6);
}
.preview-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 18px;
  border-bottom: 1px solid var(--line);
  flex-shrink: 0;
}
.preview-body {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
  background: #1d2126;
}
</style>
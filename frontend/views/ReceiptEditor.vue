<template>
  <div class="receipt-page" @dragover.prevent @drop.prevent="onDrop">
    <input type="file" ref="fileInput" @change="onFileSelect"
           accept=".jpg,.jpeg,.png,.pdf" style="display:none" />

    <ViewHeader :icon="IconReceipt" title="Receipt Editor"
      subtitle="Edit scanned receipts — background, stamps and paper texture are preserved.">
      <template #actions v-if="receipt">
        <button class="btn btn-ghost" @click="reset">Close</button>
        <button class="btn btn-primary" @click="generate"
                :disabled="generating || editCount === 0">
          {{ generating ? 'Generating…' : `Generate PDF (${editCount} edit${editCount !== 1 ? 's' : ''})` }}
        </button>
      </template>
      <template #actions v-else>
        <button class="btn btn-primary" @click="$refs.fileInput.click()">
          <IconUpload :size="13"/> Upload Receipt
        </button>
      </template>
    </ViewHeader>

    <!-- ── Drop zone ─────────────────────────────────────────────────── -->
    <div v-if="!receipt" style="padding:28px">
      <div class="drop-zone" @click="$refs.fileInput.click()">
        <IconUpload :size="32" style="color:var(--accent);margin-bottom:12px"/>
        <div style="font-size:14px;font-weight:600;margin-bottom:4px">
          Drop a receipt scan here
        </div>
        <div style="font-size:12px;color:var(--text-dim)">
          JPG · PNG · PDF &nbsp;|&nbsp; Works best at 300 DPI or higher
        </div>
        <div v-if="uploading" style="margin-top:14px;color:var(--accent);font-size:12px">
          Scanning…
        </div>
      </div>
      <div v-if="uploadError" class="error-msg">{{ uploadError }}</div>
    </div>

    <!-- ── Editor ─────────────────────────────────────────────────────── -->
    <div v-else class="editor-layout">

      <!-- Left: fields panel -->
      <div class="fields-panel">
        <div class="panel-title">Detected Fields</div>
        <div class="fields-hint">Edit values below. Changes highlight on the image →</div>

        <div v-if="knownFields.length === 0" class="no-fields">
          No structured fields detected. Use the image to click individual words.
        </div>

        <div v-for="field in knownFields" :key="fieldKey(field)" class="field-row"
             :class="{ edited: isFieldEdited(field) }">
          <div class="field-label">{{ field.field_type || field.label }}</div>
          <div class="field-original">{{ field.value || '—' }}</div>
          <input
            class="field-input"
            :placeholder="field.value || 'enter new value'"
            :value="getFieldEdit(field)"
            @input="onFieldInput(field, $event.target.value)"
            @keyup.escape="clearFieldEdit(field)"
          />
          <div v-if="isFieldEdited(field)" class="size-row">
            <span class="size-label">Size</span>
            <input type="range" class="size-slider" min="50" max="150"
                   :value="getFieldSizePct(field)"
                   @input="onFieldSizeInput(field, +$event.target.value)" />
            <span class="size-val mono">{{ getFieldSizePct(field) }}%</span>
          </div>
          <div v-if="isFieldEdited(field)" class="trim-box">
            <div class="trim-label-row">
              <span class="trim-label">Box trim</span>
              <span class="trim-hint-icon" title="trim help">?</span>
            </div>
            <div class="trim-help">
              <div class="trim-help-row"><span class="thk pos">+%</span><span class="thv">move edge inward (shrink box)</span></div>
              <div class="trim-help-row"><span class="thk neg">−%</span><span class="thv">move edge outward (expand box)</span></div>
              <div class="trim-help-row"><span class="thk">T/B</span><span class="thv">% of box height &nbsp;·&nbsp; L/R % of box width</span></div>
            </div>
            <div class="trim-diagram">
              <div class="trim-top">
                <span class="trim-side-label">T</span>
                <input type="number" class="trim-input" min="-50" max="80" step="5"
                       :value="getFieldTrim(field,'top')"
                       @change="onFieldTrimInput(field,'top',+$event.target.value)" />
              </div>
              <div class="trim-mid">
                <div class="trim-left-wrap">
                  <span class="trim-side-label">L</span>
                  <input type="number" class="trim-input" min="-50" max="80" step="5"
                         :value="getFieldTrim(field,'left')"
                         @change="onFieldTrimInput(field,'left',+$event.target.value)" />
                </div>
                <div class="trim-center-rect"></div>
                <div class="trim-right-wrap">
                  <input type="number" class="trim-input" min="-50" max="80" step="5"
                         :value="getFieldTrim(field,'right')"
                         @change="onFieldTrimInput(field,'right',+$event.target.value)" />
                  <span class="trim-side-label">R</span>
                </div>
              </div>
              <div class="trim-bottom">
                <span class="trim-side-label">B</span>
                <input type="number" class="trim-input" min="-50" max="80" step="5"
                       :value="getFieldTrim(field,'bottom')"
                       @change="onFieldTrimInput(field,'bottom',+$event.target.value)" />
              </div>
            </div>
          </div>
          <button v-if="isFieldEdited(field)" class="clear-btn"
                  @click="clearFieldEdit(field)" title="Clear edit">✕</button>
        </div>

        <div v-if="freeEdits.length > 0" style="margin-top:16px">
          <div class="panel-title" style="font-size:11px">Free Edits</div>
          <div v-for="(e, i) in freeEdits" :key="i" class="free-edit-row">
            <div class="free-edit-original">{{ e.original_text }}</div>
            <div class="free-edit-arrow">→</div>
            <div class="free-edit-new">{{ e.new_text }}</div>
            <button class="clear-btn" @click="removeFreeEdit(e)">✕</button>
          </div>
        </div>

        <!-- Appearance settings -->
        <div class="appearance-section">
          <button class="appearance-toggle" @click="showAppearance = !showAppearance">
            <span>Appearance</span>
            <span class="appearance-toggle-icon">{{ showAppearance ? '▲' : '▼' }}</span>
          </button>
          <div v-if="showAppearance" class="appearance-body">
            <div class="appearance-hint">
              Auto-detected from scan. Adjust if edited text looks too dark, blurry, or crisp.
            </div>

            <div class="ap-row">
              <label class="ap-label">Opacity</label>
              <input type="range" class="ap-slider" min="10" max="100"
                     v-model.number="appearance.opacityPct" />
              <span class="ap-val mono">{{ appearance.opacityPct }}%</span>
            </div>

            <div class="ap-row">
              <label class="ap-label">Blur</label>
              <input type="range" class="ap-slider" min="0" max="30" step="1"
                     v-model.number="appearance.blurTenths" />
              <span class="ap-val mono">{{ (appearance.blurTenths / 10).toFixed(1) }}px</span>
            </div>

            <div class="ap-row">
              <label class="ap-label">Brightness</label>
              <input type="range" class="ap-slider" min="-50" max="50"
                     v-model.number="appearance.brightness" />
              <span class="ap-val mono" :style="{ color: appearance.brightness > 0 ? 'var(--accent-2)' : appearance.brightness < 0 ? 'var(--accent-4)' : 'var(--text-dim)' }">
                {{ appearance.brightness > 0 ? '+' : '' }}{{ appearance.brightness }}
              </span>
            </div>

            <button class="ap-reset" @click="resetAppearance">Reset to auto</button>
          </div>
        </div>
      </div>

      <!-- Right: image viewer -->
      <div class="image-panel">
        <div class="image-wrapper"
             :style="{ width: receipt.preview_width + 'px', maxWidth: '100%' }"
             ref="imageWrapper">
          <img :src="'data:image/jpeg;base64,' + receipt.image_b64"
               class="receipt-img" />

          <!-- OCR span overlays (percentage-positioned) -->
          <div v-for="(span, i) in receipt.all_spans" :key="i"
               class="ocr-span"
               :class="{
                 'span-edited':   isSpanEdited(span),
                 'span-selected': selectedSpan === span,
                 'span-field':    isFieldSpan(span),
               }"
               :style="spanStyle(span)"
               @click="selectSpan(span)"
               :title="span.text">
          </div>
        </div>
      </div>
    </div>

    <!-- ── Inline edit popup ──────────────────────────────────────────── -->
    <div v-if="selectedSpan" class="edit-popup">
      <div class="edit-popup-label">
        Edit word <span class="mono" style="color:var(--accent)">{{ selectedSpan.text }}</span>
      </div>
      <input ref="editInput" v-model="editText" class="edit-popup-input mono"
             @keyup.enter="applySpanEdit" @keyup.escape="selectedSpan = null"
             placeholder="Enter new value…" />
      <div class="size-row" style="margin-top:10px">
        <span class="size-label">Size</span>
        <input type="range" class="size-slider" min="50" max="150"
               v-model.number="editSizePct" />
        <span class="size-val mono">{{ editSizePct }}%</span>
      </div>
      <div class="trim-box" style="margin-top:8px">
        <div class="trim-label-row">
          <span class="trim-label">Box trim</span>
          <span class="trim-hint-icon" title="trim help">?</span>
        </div>
        <div class="trim-help">
          <div class="trim-help-row"><span class="thk pos">+%</span><span class="thv">move edge inward (shrink box)</span></div>
          <div class="trim-help-row"><span class="thk neg">−%</span><span class="thv">move edge outward (expand box)</span></div>
          <div class="trim-help-row"><span class="thk">T/B</span><span class="thv">% of box height &nbsp;·&nbsp; L/R % of box width</span></div>
        </div>
        <div class="trim-diagram">
          <div class="trim-top">
            <span class="trim-side-label">T</span>
            <input type="number" class="trim-input" min="-50" max="80" step="5"
                   v-model.number="editBboxTrim.top" />
          </div>
          <div class="trim-mid">
            <div class="trim-left-wrap">
              <span class="trim-side-label">L</span>
              <input type="number" class="trim-input" min="-50" max="80" step="5"
                     v-model.number="editBboxTrim.left" />
            </div>
            <div class="trim-center-rect"></div>
            <div class="trim-right-wrap">
              <input type="number" class="trim-input" min="-50" max="80" step="5"
                     v-model.number="editBboxTrim.right" />
              <span class="trim-side-label">R</span>
            </div>
          </div>
          <div class="trim-bottom">
            <span class="trim-side-label">B</span>
            <input type="number" class="trim-input" min="-50" max="80" step="5"
                   v-model.number="editBboxTrim.bottom" />
          </div>
        </div>
      </div>
      <div style="display:flex;gap:8px;margin-top:8px">
        <button class="btn btn-primary" style="flex:1" @click="applySpanEdit">Apply</button>
        <button class="btn btn-ghost" @click="selectedSpan = null">Cancel</button>
      </div>
    </div>

    <!-- ── Preview modal ─────────────────────────────────────────────── -->
    <div v-if="showPreview" class="modal-overlay" @click.self="showPreview = false">
      <div class="preview-modal">
        <div class="preview-header">
          <span style="font-size:14px;font-weight:600">Review Changes</span>
          <div style="display:flex;gap:8px">
            <button class="btn btn-primary" @click="download">
              <IconDownload :size="13"/> Download PDF
            </button>
            <button class="btn btn-ghost" @click="showPreview = false">Close</button>
          </div>
        </div>
        <div class="preview-body">
          <div class="preview-col">
            <div class="preview-col-label">Original</div>
            <img :src="'data:image/jpeg;base64,' + receipt.image_b64" class="preview-img" />
          </div>
          <div class="preview-divider"></div>
          <div class="preview-col">
            <div class="preview-col-label">Edited</div>
            <img :src="'data:image/jpeg;base64,' + result.image_b64" class="preview-img" />
          </div>
        </div>
      </div>
    </div>

    <div v-if="generateError" class="error-strip">{{ generateError }}</div>
  </div>
</template>

<script>
import ViewHeader from '../components/ViewHeader.vue'
import { IconUpload, IconDownload } from '../components/icons'
import IconReceipt from '../components/icons/IconReceipt.vue'

export default {
  name: 'ReceiptEditor',
  components: { ViewHeader, IconUpload, IconDownload, IconReceipt },

  data() {
    return {
      receipt:       null,
      uploading:     false,
      uploadError:   null,
      fieldEdits:    {},
      spanEdits:     {},
      selectedSpan:  null,
      editText:      '',
      editSizePct:   100,
      editBboxTrim:  { top: 0, bottom: 0, left: 0, right: 0 },
      fieldSizePcts: {},   // fieldKey → size_pct
      fieldBboxTrims:{},   // fieldKey → { top, bottom, left, right }
      generating:    false,
      generateError: null,
      result:        null,
      showPreview:   false,
      showAppearance: false,
      appearance: {
        opacityPct:  85,   // 10–100
        blurTenths:  7,    // 0–30  (÷10 → sigma 0.0–3.0); default 0.7
        brightness:  0,    // −50 to +50
      },
    }
  },

  computed: {
    knownFields() {
      if (!this.receipt) return []
      // Show every parsed label:value pair that has an editable value box —
      // not just the ones whose label matched the HP-specific KNOWN_FIELDS
      // list. Unknown-type fields fall back to their raw OCR label for display.
      return this.receipt.fields.filter(f => f.value_bbox)
    },
    allEdits() {
      const edits = []
      // Structured field edits
      for (const field of this.knownFields) {
        const key  = this.fieldKey(field)
        const val  = this.fieldEdits[key]
        if (val !== undefined && val !== '' && val !== field.value) {
          edits.push({
            bbox:          field.value_bbox,
            new_text:      val,
            original_text: field.value,
            line_height:   field.line_height,
            label:         field.field_type,
            size_pct:      this.fieldSizePcts[key] ?? 100,
            bbox_trim:     this.fieldBboxTrims[key] || { top:0,bottom:0,left:0,right:0 },
          })
        }
      }
      // Free span edits
      for (const e of Object.values(this.spanEdits)) {
        edits.push(e)
      }
      return edits
    },
    freeEdits() {
      return Object.values(this.spanEdits)
    },
    editCount() { return this.allEdits.length },
  },

  methods: {
    // ── Upload ──────────────────────────────────────────────────────────
    onFileSelect(e) { this.upload(e.target.files[0]); e.target.value = '' },
    onDrop(e) { this.upload(e.dataTransfer.files[0]) },

    async upload(file) {
      if (!file) return
      this.uploading   = true
      this.uploadError = null
      const form = new FormData()
      form.append('file', file)
      try {
        const res = await this.$axios.post('/receipt/upload', form)
        if (res.data.success) {
          this.receipt = res.data.data
          this.fieldEdits = {}
          this.spanEdits  = {}
          this.result     = null
        } else {
          this.uploadError = res.data.data?.message || res.data.message || 'Upload failed'
        }
      } catch (err) {
        this.uploadError = err.response?.data?.data?.message || err.response?.data?.message || err.message || 'Upload failed'
      } finally {
        this.uploading = false
      }
    },

    reset() {
      this.receipt        = null
      this.fieldEdits     = {}
      this.spanEdits      = {}
      this.fieldSizePcts  = {}
      this.fieldBboxTrims = {}
      this.selectedSpan   = null
      this.editSizePct    = 100
      this.editBboxTrim   = { top:0, bottom:0, left:0, right:0 }
      this.result         = null
      this.showPreview    = false
      this.uploadError    = null
      this.generateError  = null
    },

    // ── Field helpers ────────────────────────────────────────────────────
    fieldKey(field) {
      return field.value_bbox ? field.value_bbox.join(',') : field.label
    },
    getFieldEdit(field) {
      const key = this.fieldKey(field)
      // Return saved edit if exists, otherwise pre-fill with original value
      return key in this.fieldEdits ? this.fieldEdits[key] : (field.value || '')
    },
    isFieldEdited(field) {
      const v = this.fieldEdits[this.fieldKey(field)]
      return v !== undefined && v !== '' && v !== field.value
    },
    onFieldInput(field, value) {
      this.fieldEdits[this.fieldKey(field)] = value
      // Force reactivity
      this.fieldEdits = { ...this.fieldEdits }
    },
    clearFieldEdit(field) {
      delete this.fieldEdits[this.fieldKey(field)]
      delete this.fieldSizePcts[this.fieldKey(field)]
      this.fieldEdits    = { ...this.fieldEdits }
      this.fieldSizePcts = { ...this.fieldSizePcts }
    },
    getFieldSizePct(field) {
      return this.fieldSizePcts[this.fieldKey(field)] ?? 100
    },
    onFieldSizeInput(field, val) {
      this.fieldSizePcts[this.fieldKey(field)] = val
      this.fieldSizePcts = { ...this.fieldSizePcts }
    },
    getFieldTrim(field, side) {
      return this.fieldBboxTrims[this.fieldKey(field)]?.[side] ?? 0
    },
    onFieldTrimInput(field, side, val) {
      const key = this.fieldKey(field)
      this.fieldBboxTrims[key] = { ...(this.fieldBboxTrims[key] || { top:0,bottom:0,left:0,right:0 }), [side]: val }
      this.fieldBboxTrims = { ...this.fieldBboxTrims }
    },
    isFieldSpan(span) {
      return this.knownFields.some(
        f => f.value_bbox && this.bboxOverlaps(span.bbox, f.value_bbox)
      )
    },

    // ── Span helpers ─────────────────────────────────────────────────────
    bboxKey(bbox) { return bbox.join(',') },
    bboxOverlaps(a, b) {
      return !(a[2] < b[0] || a[0] > b[2] || a[3] < b[1] || a[1] > b[3])
    },
    isSpanEdited(span) {
      return !!this.spanEdits[this.bboxKey(span.bbox)] ||
        this.knownFields.some(f => {
          const k = this.fieldKey(f)
          const v = this.fieldEdits[k]
          return v && v !== f.value && f.value_bbox &&
                 this.bboxOverlaps(span.bbox, f.value_bbox)
        })
    },
    selectSpan(span) {
      this.selectedSpan = span
      const existing    = this.spanEdits[this.bboxKey(span.bbox)]
      this.editText    = existing?.new_text   ?? span.text
      this.editSizePct = existing?.size_pct   ?? 100
      this.editBboxTrim = existing?.bbox_trim ?? { top:0, bottom:0, left:0, right:0 }
      this.$nextTick(() => this.$refs.editInput?.focus())
    },
    applySpanEdit() {
      if (!this.selectedSpan) return
      const text = this.editText
      const key  = this.bboxKey(this.selectedSpan.bbox)
      if (text !== this.selectedSpan.text) {
        this.spanEdits[key] = {
          bbox:          this.selectedSpan.bbox,
          new_text:      text,
          original_text: this.selectedSpan.text,
          line_height:   this.selectedSpan.line_height ?? this.selectedSpan.height,
          size_pct:      this.editSizePct,
          bbox_trim:     { ...this.editBboxTrim },
        }
        this.editSizePct  = 100
        this.editBboxTrim = { top:0, bottom:0, left:0, right:0 }
        this.spanEdits = { ...this.spanEdits }
      } else {
        delete this.spanEdits[key]
        this.spanEdits = { ...this.spanEdits }
      }
      this.selectedSpan = null
      this.editText     = ''
    },
    removeFreeEdit(e) {
      delete this.spanEdits[this.bboxKey(e.bbox)]
      this.spanEdits = { ...this.spanEdits }
    },

    resetAppearance() {
      this.appearance = { opacityPct: 85, blurTenths: 7, brightness: 0 }
    },

    // ── Span positioning (percentage-based so it scales with image) ──────
    spanStyle(span) {
      const iw = this.receipt.img_width
      const ih = this.receipt.img_height
      const [x0, y0, x1, y1] = span.bbox
      return {
        left:   (x0 / iw * 100) + '%',
        top:    (y0 / ih * 100) + '%',
        width:  ((x1 - x0) / iw * 100) + '%',
        height: ((y1 - y0) / ih * 100) + '%',
      }
    },

    // ── Generate ─────────────────────────────────────────────────────────
    async generate() {
      if (this.editCount === 0) return
      this.generating    = true
      this.generateError = null
      try {
        const res = await this.$axios.post('/receipt/process', {
          filepath:      this.receipt.filepath,
          edits:         this.allEdits,
          output_format: 'pdf',
          appearance: {
            opacity:     this.appearance.opacityPct / 100,
            blur:        this.appearance.blurTenths  / 10,
            brightness:  this.appearance.brightness,
            // Receipt's single printed text height, detected at scan time. Lets
            // the backend render every edit at a uniform size matching the print.
            text_height: this.receipt.text_height,
          },
        })
        if (res.data.success) {
          this.result      = res.data.data
          this.showPreview = true
        } else {
          this.generateError = res.data.data?.message || res.data.message || 'Generation failed'
        }
      } catch (err) {
        this.generateError = err.response?.data?.data?.message || err.response?.data?.message || err.message || 'Generation failed'
      } finally {
        this.generating = false
      }
    },

    download() {
      if (!this.result) return
      window.open(
        `${this.$axios.defaults.baseURL}/receipt/download/${this.result.result_filename}`,
        '_blank'
      )
    },
  },
}
</script>

<style scoped>
.receipt-page {
  display: flex;
  flex-direction: column;
  height: 100%;
  position: relative;
}
.drop-zone {
  border: 2px dashed var(--accent);
  border-radius: 8px;
  padding: 48px 32px;
  text-align: center;
  cursor: pointer;
  background: color-mix(in oklab, var(--accent) 5%, transparent);
  transition: background 0.2s;
}
.drop-zone:hover {
  background: color-mix(in oklab, var(--accent) 10%, transparent);
}

/* ── Two-column layout ── */
.editor-layout {
  flex: 1;
  display: flex;
  min-height: 0;
  overflow: hidden;
}

/* Left panel */
.fields-panel {
  width: 320px;
  min-width: 280px;
  border-right: 1px solid var(--line);
  display: flex;
  flex-direction: column;
  padding: 16px;
  gap: 6px;
  overflow-y: auto;
  background: var(--bg);
}
.panel-title {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: .06em;
  text-transform: uppercase;
  color: var(--text-mute);
  margin-bottom: 4px;
}
.fields-hint {
  font-size: 11px;
  color: var(--text-dim);
  margin-bottom: 8px;
}
.no-fields {
  font-size: 12px;
  color: var(--text-mute);
  text-align: center;
  padding: 20px 0;
}
.field-row {
  display: grid;
  grid-template-columns: 1fr auto;
  grid-template-rows: auto auto;
  gap: 2px 6px;
  padding: 8px 10px;
  border-radius: 6px;
  border: 1px solid transparent;
  background: var(--panel);
  position: relative;
}
.field-row.edited {
  border-color: var(--accent);
  background: color-mix(in oklab, var(--accent) 8%, var(--panel));
}
.field-label {
  grid-column: 1 / -1;
  font-size: 10px;
  font-weight: 600;
  color: var(--text-mute);
  text-transform: uppercase;
  letter-spacing: .05em;
}
.field-original {
  font-size: 11px;
  color: var(--text-dim);
  font-family: monospace;
  grid-column: 1;
}
.field-input {
  grid-column: 1 / -1;
  margin-top: 4px;
  background: var(--panel-2);
  border: 1px solid var(--line);
  border-radius: 4px;
  color: var(--text);
  font-size: 12px;
  font-family: 'Courier New', monospace;
  padding: 5px 7px;
  outline: none;
}
.field-input:focus { border-color: var(--accent); }
.clear-btn {
  position: absolute;
  top: 6px;
  right: 6px;
  background: none;
  border: none;
  color: var(--text-mute);
  cursor: pointer;
  font-size: 10px;
  line-height: 1;
  padding: 2px 4px;
  border-radius: 3px;
}
.clear-btn:hover { color: var(--accent-4); background: var(--panel-2); }
.free-edit-row {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  padding: 4px 6px;
  background: var(--panel);
  border-radius: 4px;
  margin-bottom: 2px;
}
.free-edit-original { color: var(--text-dim); font-family: monospace; flex: 1; }
.free-edit-arrow    { color: var(--text-mute); flex-shrink: 0; }
.free-edit-new      { color: var(--accent); font-family: monospace; flex: 1; }

/* Appearance panel */
.appearance-section {
  margin-top: 16px;
  border-top: 1px solid var(--line);
  padding-top: 10px;
}
.appearance-toggle {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  background: none;
  border: none;
  cursor: pointer;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: .06em;
  text-transform: uppercase;
  color: var(--text-mute);
  padding: 2px 0 6px;
  font-family: inherit;
}
.appearance-toggle:hover { color: var(--text); }
.appearance-toggle-icon { font-size: 9px; }
.appearance-body { display: flex; flex-direction: column; gap: 10px; }
.appearance-hint {
  font-size: 10.5px;
  color: var(--text-mute);
  line-height: 1.4;
}
.ap-row {
  display: grid;
  grid-template-columns: 68px 1fr 38px;
  align-items: center;
  gap: 8px;
}
.ap-label {
  font-size: 11px;
  color: var(--text-dim);
}
.ap-slider {
  -webkit-appearance: none;
  height: 3px;
  border-radius: 2px;
  background: var(--line-2);
  outline: none;
  cursor: pointer;
}
.ap-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  width: 13px; height: 13px;
  border-radius: 50%;
  background: var(--accent);
  cursor: pointer;
}
.ap-val {
  font-size: 11px;
  color: var(--text-dim);
  text-align: right;
}
.ap-reset {
  align-self: flex-end;
  font-size: 10.5px;
  background: none;
  border: 1px solid var(--line);
  border-radius: 4px;
  padding: 3px 8px;
  color: var(--text-mute);
  cursor: pointer;
  font-family: inherit;
}
.ap-reset:hover { color: var(--text); border-color: var(--accent); }

/* Per-edit size control */
.size-row {
  display: grid;
  grid-template-columns: 32px 1fr 38px;
  align-items: center;
  gap: 6px;
  margin-top: 4px;
}
.size-label { font-size: 10px; color: var(--text-mute); }
.size-slider {
  -webkit-appearance: none;
  height: 3px;
  border-radius: 2px;
  background: var(--line-2);
  outline: none;
  cursor: pointer;
}
.size-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  width: 11px; height: 11px;
  border-radius: 50%;
  background: var(--accent-2);
  cursor: pointer;
}
.size-val { font-size: 10px; color: var(--text-dim); text-align: right; }

/* Bbox trim box-model diagram */
.trim-box { margin-top: 6px; }
.trim-label-row {
  display: flex; align-items: center; gap: 6px; margin-bottom: 5px;
}
.trim-label {
  font-size: 10px; font-weight: 700; letter-spacing: .05em;
  text-transform: uppercase; color: var(--text-mute);
}
.trim-hint-icon {
  font-size: 9px; font-weight: 700;
  width: 14px; height: 14px; border-radius: 50%;
  background: var(--panel-3); border: 1px solid var(--line);
  color: var(--text-mute); display: inline-flex;
  align-items: center; justify-content: center; cursor: default;
  flex-shrink: 0;
}
.trim-help {
  background: var(--panel-2);
  border: 1px solid var(--line);
  border-radius: 5px;
  padding: 6px 8px;
  margin-bottom: 8px;
  display: flex; flex-direction: column; gap: 3px;
}
.trim-help-row {
  display: flex; align-items: baseline; gap: 7px; font-size: 10.5px;
}
.thk {
  font-family: var(--mono); font-size: 10px; font-weight: 700;
  min-width: 24px; padding: 1px 4px;
  border-radius: 3px; border: 1px solid var(--line);
  background: var(--panel-3); color: var(--text-dim);
  text-align: center; flex-shrink: 0;
}
.thk.pos { color: var(--accent); border-color: color-mix(in oklab, var(--accent) 35%, transparent); }
.thk.neg { color: var(--accent-4); border-color: color-mix(in oklab, var(--accent-4) 35%, transparent); }
.thv { color: var(--text-mute); font-size: 10px; line-height: 1.35; }
.trim-diagram {
  display: flex; flex-direction: column; align-items: center; gap: 4px;
}
.trim-top, .trim-bottom {
  display: flex; align-items: center; gap: 5px;
}
.trim-mid {
  display: flex; align-items: center; gap: 5px; width: 100%;
  justify-content: center;
}
.trim-left-wrap, .trim-right-wrap {
  display: flex; align-items: center; gap: 4px;
}
.trim-center-rect {
  width: 48px; height: 28px;
  border: 1.5px dashed var(--accent);
  border-radius: 3px; flex-shrink: 0;
  background: color-mix(in oklab, var(--accent) 6%, transparent);
}
.trim-side-label {
  font-size: 9px; font-weight: 700; color: var(--text-mute);
  font-family: var(--mono); min-width: 9px; text-align: center;
}
.trim-input {
  width: 44px;
  background: var(--panel-2);
  border: 1px solid var(--line);
  border-radius: 3px;
  color: var(--text);
  font-size: 11px;
  font-family: var(--mono);
  padding: 3px 4px;
  text-align: center;
  outline: none;
  -moz-appearance: textfield;
}
.trim-input::-webkit-inner-spin-button { opacity: 1; }
.trim-input:focus { border-color: var(--accent); }

/* Right image panel */
.image-panel {
  flex: 1;
  min-width: 0;
  background: #1a1d22;
  overflow: auto;
  display: flex;
  justify-content: center;
  align-items: flex-start;
  padding: 24px;
}
.image-wrapper {
  position: relative;
  flex-shrink: 0;
  box-shadow: 0 16px 48px rgba(0,0,0,.6);
}
.receipt-img {
  display: block;
  width: 100%;
  height: auto;
}

/* OCR span overlays — background-only highlight so the colon printed on the
   receipt image is clearly outside the highlighted area (no left border line
   that visually merges with the adjacent colon glyph). */
.ocr-span {
  position: absolute;
  cursor: pointer;
  border-radius: 2px;
  transition: background 0.1s;
}
.ocr-span:hover {
  background: rgba(80, 220, 120, 0.22);
}
.ocr-span.span-field {
  background: rgba(80, 220, 120, 0.06);
}
.ocr-span.span-edited {
  background: color-mix(in oklab, var(--accent) 28%, transparent);
  outline: 1.5px solid var(--accent);
  outline-offset: 1px;
}
.ocr-span.span-selected {
  background: color-mix(in oklab, var(--accent-2) 35%, transparent);
  outline: 1.5px solid var(--accent-2);
  outline-offset: 1px;
}

/* Edit popup */
.edit-popup {
  position: fixed;
  bottom: 28px;
  right: 28px;
  width: 320px;
  background: var(--panel);
  border: 1px solid var(--line);
  border-radius: 8px;
  padding: 16px;
  box-shadow: 0 12px 40px rgba(0,0,0,.5);
  z-index: 200;
}
.edit-popup-label {
  font-size: 12px;
  color: var(--text-dim);
  margin-bottom: 8px;
}
.edit-popup-input {
  width: 100%;
  box-sizing: border-box;
  background: var(--panel-2);
  border: 1px solid var(--line);
  color: var(--text);
  font-size: 13px;
  padding: 7px 9px;
  border-radius: 4px;
  outline: none;
}
.edit-popup-input:focus { border-color: var(--accent); }

/* Preview modal */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,.65);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}
.preview-modal {
  background: var(--panel);
  border: 1px solid var(--line);
  border-radius: 10px;
  width: min(1100px, 96vw);
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  box-shadow: 0 24px 60px rgba(0,0,0,.7);
}
.preview-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 20px;
  border-bottom: 1px solid var(--line);
  flex-shrink: 0;
}
.preview-body {
  flex: 1;
  overflow-y: auto;
  display: flex;
  gap: 0;
  background: #1a1d22;
}
.preview-col {
  flex: 1;
  padding: 20px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
}
.preview-col-label {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: .08em;
  text-transform: uppercase;
  color: var(--text-mute);
}
.preview-img { max-width: 100%; height: auto; display: block; }
.preview-divider {
  width: 1px;
  background: var(--line);
  flex-shrink: 0;
  margin: 20px 0;
}

/* Misc */
.error-msg {
  color: var(--accent-4);
  font-size: 12px;
  margin-top: 10px;
  text-align: center;
}
.error-strip {
  position: fixed;
  bottom: 20px;
  left: 50%;
  transform: translateX(-50%);
  background: var(--accent-4);
  color: #fff;
  padding: 10px 18px;
  border-radius: 5px;
  font-size: 13px;
  z-index: 500;
}
.btn {
  display: inline-flex; align-items: center; justify-content: center;
  gap: 6px; padding: 8px 14px; font-size: 12px; font-weight: 600;
  border-radius: 5px; cursor: pointer; border: none; font-family: inherit;
}
.btn-primary { background: var(--accent); color: #0b0d10; }
.btn-primary:hover:not(:disabled) { filter: brightness(1.1); }
.btn-primary:disabled { opacity: .45; cursor: not-allowed; }
.btn-ghost {
  background: var(--panel-2); color: var(--text);
  border: 1px solid var(--line-2);
}
.btn-ghost:hover { background: var(--panel-3); }
.mono { font-family: 'Courier New', monospace; }
</style>

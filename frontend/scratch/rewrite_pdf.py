import os

vue_file = r"c:\Users\Ajay.Gupt\Downloads\csp\projects\devtoolbox\frontend\views\PDFEditor.vue"

with open(vue_file, "r", encoding="utf-8") as f:
    lines = f.readlines()

script_lines = lines[203:474]
script_content = "".join(script_lines)

new_template = """<template>
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
          
          <div v-if="pageData && !pageLoading" class="pdf-canvas-wrapper" :style="{ opacity: isDeleted(currentPage) ? 0.3 : 1 }">
            <img :src="'data:image/png;base64,' + pageData.image" class="pdf-img" />
            
            <div 
              v-for="(span, i) in currentSpans" 
              :key="i"
              class="pdf-span"
              :class="{ 
                'edited': isEdited(span), 
                'selected': selected === span 
              }"
              :style="spanStyle(span)"
              @click="selectSpan(span)"
            ></div>
          </div>
          <div v-if="isDeleted(currentPage)" class="deleted-overlay">DELETED</div>
        </div>
        
        <div v-if="selected" class="editor-popup">
          <div style="margin-bottom: 8px; font-size: 11px; color: var(--text-dim)">
            Edit text (font: {{ selected.font }}, size: {{ selected.size.toFixed(1) }})
          </div>
          <textarea v-model="editText" class="edit-textarea mono" rows="3"></textarea>
          <div style="display: flex; gap: 8px; margin-top: 8px">
            <button @click="applyEdit('replace')" class="btn btn-primary" style="flex: 1">Replace</button>
            <button @click="applyEdit('redact')" class="btn btn-danger" style="flex: 1">Redact</button>
            <button @click="selected = null" class="btn btn-ghost">Cancel</button>
          </div>
        </div>
      </div>
    </template>

    <div v-if="uploadError" class="error-strip">{{ uploadError }}</div>
    <div v-if="saveResult" class="toast-strip">
      Save complete! <button @click="downloadResult" style="background: none; border: none; color: inherit; text-decoration: underline; cursor: pointer; font-weight: bold">Download</button>
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
</template>"""

new_style = """<style scoped>
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
  overflow: hidden;
  position: relative;
}
.sidebar {
  width: 240px;
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
  background: #1d2126;
  padding: 28px;
  display: flex;
  justify-content: center;
  overflow: auto;
  position: relative;
}
.pdf-canvas-wrapper {
  position: relative;
  box-shadow: 0 20px 60px rgba(0,0,0,0.5);
  transition: opacity 0.2s;
  /* Allow natural scaling but constrain to not be absurdly large if possible */
  max-width: fit-content;
  margin: 0 auto;
}
.pdf-img {
  display: block;
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
</style>"""

script_lines_list = script_content.splitlines()

# add imports
imports = """
import ViewHeader from '../components/ViewHeader.vue'
import Panel from '../components/Panel.vue'
import Tag from '../components/Tag.vue'
import Field from '../components/Field.vue'
import { IconPDF, IconUpload, IconFiles, IconDownload, IconHex, IconX } from '../components/icons'
"""

export_idx = -1
for i, l in enumerate(script_lines_list):
    if "export default" in l:
        export_idx = i
        break
        
script_lines_list.insert(export_idx, imports)

# add components
for i, l in enumerate(script_lines_list):
    if "export default {" in l:
        script_lines_list.insert(i+1, "  components: { ViewHeader, Panel, Tag, Field, IconPDF, IconUpload, IconFiles, IconDownload, IconHex, IconX },")
        break

final_script = "\n".join(script_lines_list)

with open(vue_file, "w", encoding="utf-8") as f:
    f.write(new_template + "\n" + final_script + "\n" + new_style)

print("Rewrote PDFEditor.vue successfully!")

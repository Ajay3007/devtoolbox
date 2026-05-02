import os

vue_file = r"c:\Users\Ajay.Gupt\Downloads\csp\projects\devtoolbox\frontend\views\FileManager.vue"

with open(vue_file, "r", encoding="utf-8") as f:
    lines = f.readlines()

script_lines = lines[100:244]
script_content = "".join(script_lines)

new_template = """<template>
  <div class="files-page">
    <ViewHeader
      :icon="IconFiles"
      title="File Manager"
      subtitle="Everything in uploads/ in one place. Rename, delete, or open any file in its matching tool."
    >
      <template #actions>
        <button class="btn btn-secondary" @click="loadFiles" :disabled="loading">
          <IconUpload :size="13" v-if="!loading" />
          <span v-else style="animation: pulse 1s infinite">●</span> Refresh
        </button>
      </template>
    </ViewHeader>

    <div class="filter-bar">
      <div style="display: flex; gap: 4px">
        <button 
          v-for="t in ['all','pcap','bin','json','pdf', 'txt']" 
          :key="t" 
          @click="filter = t" 
          class="filter-btn"
          :class="{ active: filter === t }"
        >
          {{ t }}
        </button>
      </div>
      <div class="mono" style="font-size: 11.5px; color: var(--text-dim)">
        {{ filteredFiles.length }} files · {{ formatBytes(totalFilteredSize) }} total
      </div>
    </div>

    <div class="main-grid">
      <Panel title="Files" :padding="0">
        <div v-if="loading" style="padding: 40px; text-align: center; color: var(--text-mute)">
          Loading files...
        </div>
        <div v-else-if="files.length === 0" style="padding: 40px; text-align: center; color: var(--text-mute)">
          <IconFiles :size="24" style="opacity: 0.4; margin-bottom: 10px"/>
          <div>No files found in uploads/</div>
        </div>
        <div v-else style="display: flex; flex-direction: column">
          <div class="file-table-head mono">
            <span></span><span>name</span><span>type</span><span>size</span><span>modified</span>
          </div>
          <div 
            v-for="(f, i) in filteredFiles" 
            :key="f.name" 
            @click="selectedFile = f" 
            class="file-row mono"
            :class="{ active: selectedFile?.name === f.name }"
          >
            <IconFiles :size="13" :style="{ color: getTypeColor(f.extension) }" />
            
            <span v-if="renamingFile !== f.name" class="file-name" :class="{ selected: selectedFile?.name === f.name }">{{ f.name }}</span>
            <div v-else class="rename-inline" @click.stop>
              <input 
                v-model="renameValue" 
                class="rename-input mono" 
                @keyup.enter="confirmRename(f.name)" 
                @keyup.esc="cancelRename"
                ref="renameInput"
              />
              <button @click="confirmRename(f.name)" class="btn-icon" style="color: var(--accent)"><IconCheck :size="12"/></button>
              <button @click="cancelRename" class="btn-icon" style="color: #e74c3c"><IconX :size="12"/></button>
            </div>

            <span><Tag :fg="getTypeColor(f.extension)" :bg="`color-mix(in oklab, ${getTypeColor(f.extension)} 15%, transparent)`">{{ f.extension || 'file' }}</Tag></span>
            <span style="color: var(--text-dim)">{{ formatBytes(f.size) }}</span>
            <span style="color: var(--text-mute)">{{ formatDate(f.modified) }}</span>
          </div>
        </div>
      </Panel>

      <div style="display: flex; flex-direction: column; gap: 14px; min-width: 0">
        <template v-if="selectedFile">
          <Panel title="Selected file">
            <div class="mono" style="font-size: 12px; color: var(--text-dim); line-height: 1.9">
              name   <span style="color: var(--text)">{{ selectedFile.name }}</span><br/>
              type   <span :style="{ color: getTypeColor(selectedFile.extension) }">{{ selectedFile.extension }}</span><br/>
              size   <span style="color: var(--text)">{{ selectedFile.size.toLocaleString() }} bytes</span><br/>
              path   <span style="color: var(--text)">uploads/{{ selectedFile.name }}</span><br/>
            </div>
            
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-top: 14px">
              <button v-if="isPcap(selectedFile)" @click="openInEditor(selectedFile.name)" class="btn btn-primary"><IconEditor :size="13"/>Open in Editor</button>
              <!-- Merger logic needs a route with query or we just open hex for now if it's bin -->
              <button @click="openHexViewer(selectedFile.name)" class="btn btn-primary"><IconHex :size="13"/>Open in Hex Viewer</button>
              <button @click="downloadFile(selectedFile.name)" class="btn btn-ghost"><IconDownload :size="13"/>Download</button>
            </div>
          </Panel>
          
          <Panel title="Danger zone">
            <div v-if="deleteTarget" style="margin-bottom: 10px; font-size: 12px; color: #e74c3c">
              Are you sure you want to delete {{ deleteTarget }}?
              <div style="display: flex; gap: 8px; margin-top: 8px">
                <button @click="doDelete" class="btn btn-danger" style="flex: 1" :disabled="deleting">{{ deleting ? 'Deleting...' : 'Confirm' }}</button>
                <button @click="deleteTarget = null" class="btn btn-ghost" style="flex: 1">Cancel</button>
              </div>
            </div>
            <div v-else style="display: flex; gap: 8px">
              <button @click="startRename(selectedFile)" class="btn btn-ghost" style="flex: 1" :disabled="renamingFile !== null">Rename</button>
              <button @click="confirmDelete(selectedFile.name)" class="btn btn-ghost" style="flex: 1; color: var(--accent-4); border-color: color-mix(in oklab, var(--accent-4) 25%, transparent)">Delete</button>
            </div>
          </Panel>
        </template>
        
        <Panel v-else title="Details">
          <div style="padding: 28px; text-align: center; color: var(--text-mute); font-size: 12.5px">
            <IconFiles :size="24" style="opacity: 0.4; margin-bottom: 10px"/>
            <div>Select a file to see details</div>
          </div>
        </Panel>
      </div>
    </div>
    
    <div v-if="error" class="error-strip">{{ error }}</div>
    <transition name="toast">
      <div v-if="toast" class="toast-strip">{{ toast }}</div>
    </transition>
  </div>
</template>"""

new_style = """<style scoped>
.files-page {
  display: flex;
  flex-direction: column;
  height: 100%;
}
.filter-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 28px;
  border-top: 1px solid var(--line);
  border-bottom: 1px solid var(--line);
  background: var(--bg);
}
.filter-btn {
  padding: 5px 10px;
  font-size: 11.5px;
  font-family: var(--mono);
  background: transparent;
  color: var(--text-dim);
  border: 1px solid var(--line);
  border-radius: 3px;
  cursor: pointer;
}
.filter-btn.active {
  background: color-mix(in oklab, var(--accent) 12%, transparent);
  color: var(--accent);
  border-color: color-mix(in oklab, var(--accent) 30%, transparent);
}
.main-grid {
  flex: 1;
  overflow: auto;
  padding: 18px 28px 28px;
  display: grid;
  grid-template-columns: 1.4fr 1fr;
  gap: 18px;
}
.file-table-head {
  display: grid;
  grid-template-columns: 24px 1fr 70px 100px 100px;
  gap: 10px;
  padding: 9px 14px;
  background: var(--panel-2);
  border-bottom: 1px solid var(--line);
  font-size: 10.5px;
  color: var(--text-mute);
  letter-spacing: 0.1em;
}
.file-row {
  display: grid;
  grid-template-columns: 24px 1fr 70px 100px 100px;
  gap: 10px;
  padding: 10px 14px;
  border-bottom: 1px solid color-mix(in oklab, var(--line) 50%, transparent);
  cursor: pointer;
  background: transparent;
  font-size: 11.5px;
  align-items: center;
}
.file-row.active {
  background: color-mix(in oklab, var(--accent) 8%, transparent);
}
.file-name {
  color: var(--text-dim);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.file-name.selected {
  color: var(--text);
}
.rename-inline {
  display: flex;
  align-items: center;
  gap: 4px;
}
.rename-input {
  flex: 1;
  padding: 2px 4px;
  background: var(--panel-3);
  border: 1px solid var(--accent);
  color: var(--text);
  border-radius: 3px;
  font-size: 11px;
  outline: none;
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
.btn-secondary {
  background: var(--panel-2);
  color: var(--text);
  border: 1px solid var(--line);
}
.btn-secondary:hover {
  background: var(--panel-3);
}
.btn-ghost {
  background: var(--panel-2);
  color: var(--text);
  border: 1px solid var(--line-2);
}
.btn-ghost:hover:not(:disabled) {
  background: var(--panel-3);
}
.btn-danger {
  background: #e74c3c;
  color: white;
}
.btn-danger:hover:not(:disabled) {
  filter: brightness(1.1);
}
.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.btn-icon {
  background: none;
  border: none;
  cursor: pointer;
  padding: 2px;
  display: inline-flex;
}
.error-strip, .toast-strip {
  position: fixed;
  bottom: 20px;
  left: 50%;
  transform: translateX(-50%);
  padding: 8px 16px;
  border-radius: 5px;
  font-size: 13px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.2);
  z-index: 1000;
}
.error-strip {
  background: var(--accent-3);
  color: #fff;
}
.toast-strip {
  background: var(--accent);
  color: #0b0d10;
}
.toast-enter-active, .toast-leave-active { transition: all 0.3s ease; }
.toast-enter-from, .toast-leave-to { opacity: 0; transform: translateY(10px); }
</style>"""

script_lines_list = script_content.splitlines()

# add imports
imports = """
import ViewHeader from '../components/ViewHeader.vue'
import Panel from '../components/Panel.vue'
import Tag from '../components/Tag.vue'
import { IconFiles, IconUpload, IconEditor, IconMerger, IconHex, IconDownload, IconCheck, IconX } from '../components/icons'
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
        script_lines_list.insert(i+1, "  components: { ViewHeader, Panel, Tag, IconFiles, IconUpload, IconEditor, IconMerger, IconHex, IconDownload, IconCheck, IconX },")
        break

# add extra data properties
data_idx = -1
for i, l in enumerate(script_lines_list):
    if "data() {" in l or "data () {" in l:
        data_idx = i
        break

if data_idx != -1:
    extra_data = """      selectedFile: null,
      filter: 'all',"""
    script_lines_list.insert(data_idx + 2, extra_data)

# add computed properties for filtering
computed_idx = -1
for i, l in enumerate(script_lines_list):
    if "computed: {" in l:
        computed_idx = i
        break

extra_computed = """    filteredFiles() {
      if (this.filter === 'all') return this.files;
      return this.files.filter(f => f.extension === this.filter || (this.filter === 'bin' && ['bin', 'exe', 'dat'].includes(f.extension)));
    },
    totalFilteredSize() {
      return this.filteredFiles.reduce((sum, f) => sum + f.size, 0);
    },"""

if computed_idx != -1:
    script_lines_list.insert(computed_idx + 1, extra_computed)
else:
    # insert computed before methods
    for i, l in enumerate(script_lines_list):
        if "methods: {" in l:
            script_lines_list.insert(i, "  computed: {\n" + extra_computed + "\n  },")
            break

# add methods
methods_idx = -1
for i, l in enumerate(script_lines_list):
    if "methods: {" in l:
        methods_idx = i
        break

extra_methods = """    getTypeColor(ext) {
      const typeColors = {
        pcap: 'var(--accent)', pcapng: 'var(--accent)',
        bin: 'var(--accent-2)',
        json: 'var(--accent-5)',
        pdf: 'var(--accent-3)',
        txt: 'var(--accent-4)'
      };
      return typeColors[ext] || 'var(--text-mute)';
    },"""

if methods_idx != -1:
    script_lines_list.insert(methods_idx + 1, extra_methods)

# Update confirmDelete so it unselects the file if we delete it
for i, l in enumerate(script_lines_list):
    if "this.deleteTarget = null;" in l and "this.loadFiles();" in script_lines_list[i+1]:
        script_lines_list.insert(i, "          if (this.selectedFile?.name === this.deleteTarget) this.selectedFile = null;")
        break

final_script = "\n".join(script_lines_list)

with open(vue_file, "w", encoding="utf-8") as f:
    f.write(new_template + "\n" + final_script + "\n" + new_style)

print("Rewrote FileManager.vue successfully!")

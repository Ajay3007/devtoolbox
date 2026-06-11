<template>
  <div class="merger-page">
    <ViewHeader
      :icon="IconMerger"
      title="PCAP Merger"
      subtitle="Combine multiple PCAP/PCAPNG files into one. Timing and order preserved."
    />
    <div class="main-grid">
      <!-- LEFT: input files -->
      <div class="col">
        <Panel title="Input files" :subtitle="`${selectedFiles.length} queued · merge requires 2+`">
          <!-- Drop zone -->
          <div 
            class="drop-zone" 
            @click="$refs.fileInput.click()"
            @dragover.prevent
            @drop.prevent="handleFileDrop"
          >
            <IconUpload :size="22" style="color: var(--text-mute); margin-bottom: 8px" />
            <div style="font-size: 13px; color: var(--text-dim)">Drop PCAP/PCAPNG files or click to browse</div>
            <input type="file" ref="fileInput" @change="handleFileSelect" multiple accept=".pcap,.pcapng" style="display: none" />
          </div>

          <div style="display: flex; flex-direction: column; gap: 6px">
            <div v-for="(f, i) in selectedFiles" :key="f.name + i" class="file-item">
              <span class="mono" style="font-size: 10.5px; color: var(--text-mute); width: 22px">{{ String(i+1).padStart(2,'0') }}</span>
              <IconFiles :size="13" style="color: var(--accent-3)" />
              <span class="mono" style="font-size: 12px; flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap">{{ f.name }}</span>
              <span class="mono" style="font-size: 11px; color: var(--text-mute)">{{ formatBytes(f.size) }}</span>
              <button @click="removeFile(i)" class="remove-btn">
                <IconX :size="13" />
              </button>
            </div>
          </div>
        </Panel>
      </div>

      <!-- RIGHT: Output configuration -->
      <div class="col">
        <Panel title="Output" subtitle="Merged file configuration">
          <Field label="output filename" v-model="outputName" placeholder="merged.pcap" />
          <div style="margin-top: 12px; display: grid; grid-template-columns: 1fr 1fr; gap: 8px">
            <MiniStat label="sources" :value="selectedFiles.length" />
            <MiniStat label="total files" :value="selectedFiles.length" color="var(--accent)" />
            <MiniStat label="est. size" :value="formatBytes(totalSize)" />
            <MiniStat label="ordering" value="chronological" />
          </div>

          <button @click="mergeFiles" :disabled="!canMerge || merging" class="merge-btn">
            <template v-if="merging">
              <span style="animation: pulse 1s infinite">●</span> Merging...
            </template>
            <template v-else>
              <IconMerger :size="14"/> Merge {{ selectedFiles.length }} file{{ selectedFiles.length === 1 ? '' : 's' }}
            </template>
          </button>
          
          <div v-if="error" style="color: #e74c3c; font-size: 12px; margin-top: 8px;">{{ error }}</div>
        </Panel>

        <Panel v-if="result" title="Merge complete">
          <div class="success-panel">
            <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 6px">
              <IconCheck :size="15" style="color: var(--accent)" />
              <span class="mono" style="font-size: 12px">{{ result.filepath.split('/').pop() }}</span>
            </div>
            <div class="mono" style="font-size: 11px; color: var(--text-dim)">
              {{ result.message || 'Successfully merged files.' }}
            </div>
          </div>
          <div style="display: flex; gap: 8px">
            <button @click="downloadFile" class="btn btn-primary" style="flex: 1"><IconDownload :size="13"/> Download</button>
            <button @click="openInEditor" class="btn btn-ghost" style="flex: 1"><IconEditor :size="13"/> Open in Editor</button>
          </div>
        </Panel>

        <Panel title="Timeline preview" subtitle="How packets interleave">
          <div style="display: flex; flex-direction: column; gap: 8px">
            <div v-for="(f, i) in selectedFiles" :key="f.name + i">
              <div class="mono" style="font-size: 11px; color: var(--text-dim); margin-bottom: 4px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap">{{ f.name }}</div>
              <div class="timeline-track">
                <!-- Visual representation of file in timeline -->
                <div class="timeline-bar" :style="{ background: getTrackColor(i) }"></div>
              </div>
            </div>
            <div v-if="result">
              <div class="mono" style="font-size: 11px; color: var(--accent); margin-bottom: 4px">→ merged output</div>
              <div class="timeline-track merged-track">
                 <!-- Interleaved visual -->
                 <div v-for="j in 20" :key="j" class="merged-tick" :style="{ left: (j/20*100)+'%', background: getTrackColor(j % selectedFiles.length) }"></div>
              </div>
            </div>
          </div>
        </Panel>
      </div>
    </div>
  </div>
</template>
<script>
import axios from 'axios';


import ViewHeader from '../components/ViewHeader.vue'
import Panel from '../components/Panel.vue'
import Field from '../components/Field.vue'
import MiniStat from '../components/MiniStat.vue'
import { IconMerger, IconUpload, IconFiles, IconX, IconCheck, IconDownload, IconEditor } from '../components/icons'

export default {
  components: { ViewHeader, Panel, Field, MiniStat, IconMerger, IconUpload, IconFiles, IconX, IconCheck, IconDownload, IconEditor },
  name: 'PCAPMerger',
  data() {
    return {
      selectedFiles: [],
      outputName: '',
      merging: false,
      result: null,
      error: null
    };
  },
  computed: {
    totalSize() {
      return this.selectedFiles.reduce((sum, f) => sum + f.size, 0);
    },
    canMerge() {
      return this.selectedFiles.length >= 2;
    }
  },
  methods: {
    handleFileDrop(e) {
      this.error = null;
      const files = Array.from(e.dataTransfer.files).filter(f => f.name.endsWith('.pcap') || f.name.endsWith('.pcapng'));
      if (files.length > 0) {
        this.selectedFiles = [...this.selectedFiles, ...files];
      }
      this.result = null;
    },
    getTrackColor(i) {
      const colors = ['var(--accent)', 'var(--accent-2)', 'var(--accent-4)', 'var(--accent-5)'];
      return colors[i % colors.length];
    },
    handleFileSelect(event) {
      this.error = null;
      const files = Array.from(event.target.files || []);
      this.selectedFiles = [...this.selectedFiles, ...files];
      this.result = null;
    },
    removeFile(index) {
      this.selectedFiles.splice(index, 1);
      this.result = null;
    },
    async mergeFiles() {
      if (!this.canMerge) return;
      this.merging = true;
      this.error = null;
      this.result = null;

      try {
        const formData = new FormData();
        this.selectedFiles.forEach(file => formData.append('files', file));
        if (this.outputName) {
          formData.append('output_name', this.outputName);
        }

        const response = await this.$axios.post('/pcap/merge', formData, {
          headers: { 'Content-Type': 'multipart/form-data' }
        });

        if (response.data.success) {
          this.result = response.data.data;
        } else {
          this.error = response.data.data?.message || response.data.message || 'Failed to merge files';
        }
      } catch (err) {
        this.error = err.response?.data?.data?.message || err.response?.data?.message || err.message || 'Failed to merge files';
      } finally {
        this.merging = false;
      }
    },
    resetForm() {
      this.selectedFiles = [];
      this.outputName = '';
      this.result = null;
      this.error = null;
      this.merging = false;
      const input = document.getElementById('pcapFiles');
      if (input) input.value = '';
    },
    async downloadFile() {
      if (!this.result) return;
      try {
        const response = await this.$axios.get(
          `/pcap/export/${encodeURIComponent(this.result.filepath)}`,
          { responseType: 'blob' }
        );

        const url = window.URL.createObjectURL(new Blob([response.data]));
        const link = document.createElement('a');
        link.href = url;
        link.setAttribute('download', this.result.filepath.split('/').pop());
        document.body.appendChild(link);
        link.click();
        link.remove();
        window.URL.revokeObjectURL(url);
      } catch (err) {
        this.error = 'Failed to download file';
      }
    },
    openInEditor() {
      if (this.result) {
        this.$router.push({
          name: 'pcap-editor',
          query: { file: this.result.filepath }
        });
      }
    },
    formatBytes(bytes) {
      if (!bytes) return '0 B';
      const sizes = ['B', 'KB', 'MB', 'GB'];
      const i = Math.min(Math.floor(Math.log(bytes) / Math.log(1024)), sizes.length - 1);
      const value = bytes / Math.pow(1024, i);
      return `${value.toFixed(1)} ${sizes[i]}`;
    }
  }
};
</script>
<style scoped>
.merger-page {
  display: flex;
  flex-direction: column;
  height: 100%;
}
.main-grid {
  padding: 8px 28px 28px;
  display: grid;
  grid-template-columns: 1.2fr 1fr;
  gap: 18px;
  flex: 1;
  min-height: 0;
  overflow: auto;
}
.col {
  display: flex;
  flex-direction: column;
  gap: 14px;
}
.drop-zone {
  border: 2px dashed var(--line-2);
  border-radius: 6px;
  padding: 18px;
  text-align: center;
  margin-bottom: 12px;
  background: var(--bg);
  cursor: pointer;
  transition: all 0.2s;
}
.drop-zone:hover {
  background: var(--panel-2);
  border-color: var(--accent);
}
.file-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  background: var(--panel-2);
  border: 1px solid var(--line);
  border-radius: 5px;
}
.remove-btn {
  background: transparent;
  border: none;
  color: var(--text-mute);
  padding: 2px;
  cursor: pointer;
}
.remove-btn:hover {
  color: #e74c3c;
}
.merge-btn {
  width: 100%;
  margin-top: 14px;
  padding: 11px 16px;
  font-size: 13px;
  font-weight: 600;
  border: none;
  border-radius: 6px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 7px;
  background: var(--accent);
  color: #0b0d10;
  cursor: pointer;
  transition: filter 0.2s;
}
.merge-btn:hover:not(:disabled) {
  filter: brightness(1.1);
}
.merge-btn:disabled {
  background: var(--panel-3);
  color: var(--text-mute);
  cursor: not-allowed;
}
.success-panel {
  padding: 12px 14px;
  background: color-mix(in oklab, var(--accent) 8%, transparent);
  border: 1px solid color-mix(in oklab, var(--accent) 25%, transparent);
  border-radius: 5px;
  margin-bottom: 12px;
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
.btn-ghost {
  background: var(--panel-2);
  color: var(--text);
  border: 1px solid var(--line-2);
}
.btn-ghost:hover {
  background: var(--panel-3);
}
.timeline-track {
  position: relative;
  height: 14px;
  background: var(--panel-3);
  border-radius: 2px;
  overflow: hidden;
}
.timeline-bar {
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 100%;
  opacity: 0.7;
}
.merged-track {
  display: flex;
}
.merged-tick {
  position: absolute;
  top: 0;
  bottom: 0;
  width: 2px;
}
@keyframes pulse {
  0% { opacity: 1; }
  50% { opacity: 0.5; }
  100% { opacity: 1; }
}
</style>
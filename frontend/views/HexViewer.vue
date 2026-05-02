<template>
  <div class="hex-page" @dragover.prevent @drop.prevent="handleFileDrop">
    <!-- Hidden file input -->
    <input type="file" ref="fileInput" @change="handleFileUpload" style="display: none" />
    
    <ViewHeader
      :icon="IconHex"
      title="Hex Viewer"
      subtitle="Inspect any binary. Auto-detects JSON, XML, text, and binary."
    >
      <template #actions v-if="!fileData">
        <button class="btn btn-primary" @click="$refs.fileInput.click()">
          <IconUpload :size="13"/> Upload File
        </button>
      </template>
    </ViewHeader>

    <template v-if="!fileData">
      <div style="padding: 28px">
        <div class="drop-zone" @click="$refs.fileInput.click()">
          <IconUpload :size="32" style="color: var(--accent); margin-bottom: 12px" />
          <div style="font-size: 14px; font-weight: 500; margin-bottom: 4px; color: var(--text)">Drop a file here to view its hex dump</div>
          <div style="font-size: 12px; color: var(--text-dim)">Or click to browse</div>
          
          <div v-if="uploadProgress" style="margin-top: 14px; color: var(--accent); font-size: 12px">
            Loading... {{ uploadProgress }}%
          </div>
        </div>
      </div>
    </template>
    
    <template v-else>
      <div class="file-bar">
        <div style="display: flex; align-items: center; gap: 10px; min-width: 0">
          <IconFiles :size="14" style="color: var(--accent-2)" />
          <span class="mono" style="font-size: 12px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis">{{ fileData.filename }}</span>
          <Tag fg="var(--text-dim)">{{ formatBytes(fileData.size) }}</Tag>
          <Tag fg="var(--accent-2)" bg="color-mix(in oklab, var(--accent-2) 15%, transparent)">{{ fileData.type || 'BINARY' }}</Tag>
          <Tag fg="var(--text-dim)">offset {{ formatOffset(currentOffset) }}</Tag>
        </div>
        <div style="display: flex; gap: 4px">
          <button @click="viewMode = 'text'" class="toggle-btn" :class="{ active: viewMode === 'text' }" :disabled="!fileData.text">Text</button>
          <button @click="viewMode = 'hex'" class="toggle-btn" :class="{ active: viewMode === 'hex' }">Hex</button>
          <button @click="viewMode = 'split'" class="toggle-btn" :class="{ active: viewMode === 'split' }" :disabled="!fileData.text">Split</button>
          <button @click="closeFile" class="toggle-btn" style="margin-left: 8px">Close</button>
        </div>
      </div>

      <div class="toolbar">
        <div class="search-box">
          <IconSearch :size="13" style="color: var(--text-mute)" />
          <input
            placeholder="search ascii or 0xDE AD BE EF"
            v-model="searchQuery"
            @keyup.enter="searchHex"
            class="mono search-input"
          />
          <button v-if="searchQuery" @click="clearSearch" style="background: none; border: none; color: var(--text-mute); cursor: pointer"><IconX :size="12"/></button>
          <span v-if="searchResults.length > 0" class="mono" style="font-size: 11px; color: var(--accent)">{{ searchResults.length }} hits</span>
        </div>
        <div style="display: flex; align-items: center; gap: 8px">
          <button @click="prevPage" class="pag-btn" :disabled="currentPage <= 1">◀</button>
          <span class="mono" style="font-size: 11.5px; color: var(--text-dim)">
            page {{ currentPage }} / {{ totalPages }}
          </span>
          <button @click="nextPage" class="pag-btn" :disabled="currentPage >= totalPages">▶</button>
          <div style="width: 1px; height: 18px; background: var(--line); margin: 0 4px"></div>
          <button @click="copyToClipboard" class="btn btn-ghost" style="padding: 5px 10px" :disabled="!fileData.text"><IconCopy :size="12"/> Copy</button>
          <button @click="viewMode === 'text' ? downloadTextContent() : downloadAsText()" class="btn btn-ghost" style="padding: 5px 10px"><IconDownload :size="12"/> Export</button>
        </div>
      </div>

      <div class="view-area">
        <div v-if="viewMode === 'hex' || viewMode === 'split'" class="hex-pane">
          <div class="hex-dump mono">
            <div class="hex-head">
              <span style="width: 65px">offset</span>
              <span style="flex: 1">00 01 02 03  04 05 06 07  08 09 0a 0b  0c 0d 0e 0f</span>
              <span style="width: 130px; text-align: right">ascii</span>
            </div>
            
            <div v-for="(row, i) in displayRows" :key="i" class="hex-row">
              <span class="hex-offset">{{ formatOffset(row.offset).replace('0x', '') }}</span>
              <span class="hex-bytes">
                <span 
                  v-for="(b, j) in row.bytes" 
                  :key="j"
                  :class="{ 
                    highlight: isHighlighted(row.offset + j),
                    printable: b !== '  ' && parseInt(b, 16) >= 32 && parseInt(b, 16) <= 126
                  }"
                  @click="selectByte(row.offset + j)"
                >
                  {{ b }}{{ j === 3 || j === 7 || j === 11 ? '  ' : ' ' }}
                </span>
              </span>
              <span class="hex-ascii">
                <span 
                  v-for="(char, j) in row.ascii" 
                  :key="j"
                  :class="{ 
                    highlight: isHighlighted(row.offset + j),
                    printable: char !== '.' && char !== ' '
                  }"
                  @click="selectByte(row.offset + j)"
                >{{ char }}</span>
              </span>
            </div>
          </div>
        </div>
        
        <div v-if="(viewMode === 'text' || viewMode === 'split') && fileData.text" class="text-pane">
          <pre class="text-content mono">{{ fileData.text }}</pre>
        </div>
      </div>
    </template>
    
    <div v-if="error" class="error-strip">{{ error }}</div>
  </div>
</template>
<script>
import axios from 'axios';


import ViewHeader from '../components/ViewHeader.vue'
import Tag from '../components/Tag.vue'
import { IconHex, IconUpload, IconFiles, IconSearch, IconX, IconCopy, IconDownload } from '../components/icons'

export default {
  components: { ViewHeader, Tag, IconHex, IconUpload, IconFiles, IconSearch, IconX, IconCopy, IconDownload },
  name: 'HexViewer',
  data() {
    return {
      fileData: null,
      uploadProgress: 0,
      error: null,
      currentOffset: 0,
      bytesPerPage: 256,
      searchQuery: '',
      searchResults: [],
      selectedByte: null,
      viewMode: 'text' // 'text' or 'hex'
    };
  },
  computed: {
    displayRows() {
      if (!this.fileData || !this.fileData.hex) return [];
      
      const rows = [];
      const hexData = this.fileData.hex;
      const startIdx = this.currentOffset * 2; // Each byte is 2 hex chars
      const endIdx = Math.min(startIdx + this.bytesPerPage * 2, hexData.length);
      
      for (let i = startIdx; i < endIdx; i += 32) { // 32 hex chars = 16 bytes
        const rowHex = hexData.substring(i, Math.min(i + 32, endIdx));
        const bytes = [];
        const ascii = [];
        
        for (let j = 0; j < 32; j += 2) {
          if (j < rowHex.length) {
            const byte = rowHex.substring(j, j + 2);
            bytes.push(byte);
            
            const charCode = parseInt(byte, 16);
            ascii.push(charCode >= 32 && charCode <= 126 ? String.fromCharCode(charCode) : '.');
          } else {
            bytes.push('  ');
            ascii.push(' ');
          }
        }
        
        rows.push({
          offset: this.currentOffset + (i - startIdx) / 2,
          bytes,
          ascii
        });
      }
      
      return rows;
    },
    currentPage() {
      return Math.floor(this.currentOffset / this.bytesPerPage) + 1;
    },
    totalPages() {
      return this.fileData ? Math.ceil(this.fileData.size / this.bytesPerPage) : 0;
    }
  },
  methods: {
    handleFileUpload(event) {
      const file = event.target.files[0];
      if (file) {
        this.uploadFile(file);
      }
    },
    handleFileDrop(event) {
      event.preventDefault();
      const file = event.dataTransfer.files[0];
      if (file) {
        this.uploadFile(file);
      }
    },
    async uploadFile(file) {
      const formData = new FormData();
      formData.append('file', file);
      
      this.uploadProgress = 0;
      this.error = null;
      
      try {
        const response = await this.$axios.post('/hex/upload', formData, {
          headers: { 'Content-Type': 'multipart/form-data' },
          onUploadProgress: (progressEvent) => {
            this.uploadProgress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          }
        });
        
        if (response.data.success) {
          this.fileData = response.data;
          this.currentOffset = 0;
          this.searchResults = [];
          // Default to text view if text content is available
          this.viewMode = response.data.text ? 'text' : 'hex';
        } else {
          this.error = response.data.data?.message || response.data.message || 'Failed to load file';
        }
      } catch (err) {
        this.error = err.response?.data?.data?.message || err.response?.data?.message || err.message || 'Failed to upload file';
      } finally {
        this.uploadProgress = 0;
      }
    },
    closeFile() {
      this.fileData = null;
      this.currentOffset = 0;
      this.searchQuery = '';
      this.searchResults = [];
      this.selectedByte = null;
      this.error = null;
      this.viewMode = 'text';
    },
    nextPage() {
      if (this.currentOffset + this.bytesPerPage < this.fileData.size) {
        this.currentOffset += this.bytesPerPage;
      }
    },
    prevPage() {
      if (this.currentOffset >= this.bytesPerPage) {
        this.currentOffset -= this.bytesPerPage;
      } else {
        this.currentOffset = 0;
      }
    },
    goToOffset(offset) {
      this.currentOffset = Math.floor(offset / this.bytesPerPage) * this.bytesPerPage;
      this.selectedByte = offset;
    },
    searchHex() {
      if (!this.searchQuery || !this.fileData) return;
      
      this.searchResults = [];
      let searchHex = this.searchQuery.trim().replace(/\s+/g, '');
      
      // Convert ASCII to hex if not already hex
      if (!/^[0-9A-Fa-f]+$/.test(searchHex)) {
        searchHex = Array.from(searchHex)
          .map(char => char.charCodeAt(0).toString(16).padStart(2, '0'))
          .join('');
      }
      
      searchHex = searchHex.toUpperCase();
      const hexData = this.fileData.hex.toUpperCase();
      
      let index = hexData.indexOf(searchHex);
      while (index !== -1 && this.searchResults.length < 100) {
        this.searchResults.push(index / 2);
        index = hexData.indexOf(searchHex, index + 2);
      }
      
      if (this.searchResults.length > 0) {
        this.goToOffset(this.searchResults[0]);
      } else {
        this.error = 'Pattern not found';
        setTimeout(() => this.error = null, 3000);
      }
    },
    clearSearch() {
      this.searchQuery = '';
      this.searchResults = [];
      this.selectedByte = null;
    },
    isHighlighted(offset) {
      return this.searchResults.includes(offset) || this.selectedByte === offset;
    },
    selectByte(offset) {
      this.selectedByte = offset;
    },
    formatOffset(offset) {
      return '0x' + offset.toString(16).toUpperCase().padStart(8, '0');
    },
    formatBytes(bytes) {
      if (!bytes) return '0 B';
      const sizes = ['B', 'KB', 'MB', 'GB'];
      const i = Math.min(Math.floor(Math.log(bytes) / Math.log(1024)), sizes.length - 1);
      const value = bytes / Math.pow(1024, i);
      return `${value.toFixed(2)} ${sizes[i]}`;
    },
    downloadAsText() {
      if (!this.fileData) return;
      
      let text = `Hex Dump: ${this.fileData.filename}\n`;
      text += `Size: ${this.fileData.size} bytes\n\n`;
      text += 'Offset    00 01 02 03 04 05 06 07 08 09 0A 0B 0C 0D 0E 0F  ASCII\n';
      text += '--------  -----------------------------------------------  ----------------\n';
      
      const hexData = this.fileData.hex;
      for (let i = 0; i < hexData.length; i += 32) {
        const offset = (i / 2).toString(16).toUpperCase().padStart(8, '0');
        const rowHex = hexData.substring(i, Math.min(i + 32, hexData.length));
        const bytes = rowHex.match(/.{1,2}/g) || [];
        const hexPart = bytes.join(' ').padEnd(47, ' ');
        
        const ascii = bytes.map(byte => {
          const charCode = parseInt(byte, 16);
          return charCode >= 32 && charCode <= 126 ? String.fromCharCode(charCode) : '.';
        }).join('');
        
        text += `${offset}  ${hexPart}  ${ascii}\n`;
      }
      
      const blob = new Blob([text], { type: 'text/plain' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `${this.fileData.filename}.hex.txt`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    },
    downloadTextContent() {
      if (!this.fileData || !this.fileData.text) return;
      
      const blob = new Blob([this.fileData.text], { type: 'text/plain' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `${this.fileData.filename}.txt`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    },
    copyToClipboard() {
      if (!this.fileData || !this.fileData.text) return;
      
      navigator.clipboard.writeText(this.fileData.text).then(() => {
        alert('Content copied to clipboard!');
      }).catch(err => {
        this.error = 'Failed to copy to clipboard';
      });
    }
  }
};
</script>
<style scoped>
.hex-page {
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
.toggle-btn {
  padding: 5px 12px;
  font-size: 11.5px;
  font-family: var(--mono);
  background: var(--panel-2);
  color: var(--text-dim);
  border: 1px solid var(--line);
  border-radius: 3px;
  cursor: pointer;
}
.toggle-btn.active {
  background: color-mix(in oklab, var(--accent) 12%, transparent);
  color: var(--accent);
  border-color: color-mix(in oklab, var(--accent) 30%, transparent);
}
.toggle-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 28px;
  border-bottom: 1px solid var(--line);
  background: var(--bg);
}
.search-box {
  display: flex;
  align-items: center;
  gap: 7px;
  padding: 5px 10px;
  background: var(--panel-2);
  border: 1px solid var(--line);
  border-radius: 4px;
  width: 340px;
}
.search-input {
  flex: 1;
  background: transparent;
  border: none;
  outline: none;
  color: var(--text);
  font-size: 12px;
}
.pag-btn {
  width: 24px;
  height: 24px;
  padding: 0;
  font-size: 10px;
  background: var(--panel-2);
  color: var(--text-dim);
  border: 1px solid var(--line);
  border-radius: 3px;
  cursor: pointer;
}
.pag-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}
.view-area {
  flex: 1;
  overflow: auto;
  padding: 18px 28px 28px;
  display: grid;
  gap: 14px;
}
.view-area:has(> .hex-pane:first-child:nth-last-child(2)) {
  grid-template-columns: 1fr 1fr;
}
.hex-pane, .text-pane {
  min-width: 0;
}
.hex-dump {
  background: var(--bg);
  border: 1px solid var(--line);
  border-radius: 5px;
  padding: 14px;
  font-size: 12px;
  line-height: 1.75;
}
.hex-head {
  display: flex;
  gap: 14px;
  color: var(--text-mute);
  font-size: 10.5px;
  letter-spacing: 0.1em;
  border-bottom: 1px solid var(--line);
  padding-bottom: 6px;
  margin-bottom: 8px;
}
.hex-row {
  display: flex;
  gap: 14px;
}
.hex-offset {
  width: 65px;
  color: var(--text-mute);
}
.hex-bytes {
  flex: 1;
}
.hex-bytes span, .hex-ascii span {
  color: var(--text-dim);
  border-radius: 2px;
  cursor: pointer;
}
.hex-bytes span.printable {
  color: var(--accent-2);
}
.hex-ascii span.printable {
  color: var(--text);
}
.hex-bytes span.highlight, .hex-ascii span.highlight {
  color: var(--accent);
  background: color-mix(in oklab, var(--accent) 20%, transparent);
}
.hex-ascii {
  width: 130px;
  text-align: right;
  letter-spacing: 2px;
}
.text-content {
  background: var(--bg);
  border: 1px solid var(--line);
  border-radius: 5px;
  padding: 14px;
  font-size: 12.5px;
  line-height: 1.7;
  color: var(--text-dim);
  margin: 0;
  white-space: pre-wrap;
  word-break: break-all;
  height: 100%;
  box-sizing: border-box;
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
.btn-ghost:hover:not(:disabled) {
  background: var(--panel-3);
}
.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.error-strip {
  position: fixed;
  bottom: 20px;
  left: 50%;
  transform: translateX(-50%);
  background: var(--accent-3);
  color: #fff;
  padding: 8px 16px;
  border-radius: 5px;
  font-size: 13px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.2);
  z-index: 1000;
}
</style>
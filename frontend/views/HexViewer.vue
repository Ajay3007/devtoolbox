<template>
  <div class="hex-viewer-container">
    <h1>Hex Viewer</h1>
    <p class="subtitle">View and analyze binary files in hexadecimal format</p>

    <!-- Upload Section -->
    <section v-if="!fileData" class="upload-section">
      <div class="upload-box" @dragover.prevent @drop.prevent="handleFileDrop">
        <input
          type="file"
          ref="fileInput"
          @change="handleFileUpload"
          style="display: none"
        />
        <div @click="$refs.fileInput.click()" class="upload-content">
          <div class="upload-icon">🔍</div>
          <h3>Upload Binary File</h3>
          <p>Drag and drop or click to browse</p>
          <p class="file-formats">All file types supported</p>
        </div>
      </div>

      <div v-if="uploadProgress" class="progress-section">
        <div class="progress-bar">
          <div class="progress-fill" :style="{ width: uploadProgress + '%' }"></div>
        </div>
        <p>{{ uploadProgress }}% uploaded</p>
      </div>
    </section>

    <!-- Hex Display Section -->
    <section v-if="fileData" class="hex-display-section">
      <div class="file-info">
        <div class="info-row">
          <strong>File:</strong> {{ fileData.filename }}
          <button @click="closeFile" class="btn-close">✕ Close</button>
        </div>
        <div class="info-row">
          <strong>Size:</strong> {{ formatBytes(fileData.size) }} ({{ fileData.size }} bytes)
        </div>
        <div class="info-row">
          <strong>Type:</strong> 
          <span class="badge" :class="'badge-' + fileData.file_type">
            {{ fileData.file_type.toUpperCase() }}
          </span>
          <span v-if="fileData.encoding" class="encoding-info">
            ({{ fileData.encoding }})
          </span>
        </div>
        <div v-if="!viewMode && fileData.text" class="info-row">
          <strong>Showing:</strong> Bytes {{ currentOffset }} - {{ Math.min(currentOffset + bytesPerPage, fileData.size) }}
        </div>
      </div>

      <!-- View Mode Toggle -->
      <div v-if="fileData.text" class="view-toggle">
        <button 
          @click="viewMode = 'text'" 
          :class="['toggle-btn', { active: viewMode === 'text' }]"
        >
          📄 Text View
        </button>
        <button 
          @click="viewMode = 'hex'" 
          :class="['toggle-btn', { active: viewMode === 'hex' }]"
        >
          🔢 Hex View
        </button>
      </div>

      <!-- Text View -->
      <div v-if="viewMode === 'text' && fileData.text" class="text-view">
        <div class="text-header">
          <span>Human-Readable Content</span>
          <button @click="copyToClipboard" class="btn btn-secondary btn-sm">📋 Copy</button>
        </div>
        <pre class="text-content" :class="'format-' + fileData.file_type">{{ fileData.text }}</pre>
      </div>

      <!-- Search -->
      <div v-if="viewMode === 'hex'" class="search-section">
        <input
          v-model="searchQuery"
          type="text"
          placeholder="Search hex (e.g., 4D5A or MZ)"
          class="search-input"
          @keyup.enter="searchHex"
        />
        <button @click="searchHex" class="btn btn-primary">🔍 Search</button>
        <button v-if="searchResults.length" @click="clearSearch" class="btn btn-secondary">Clear</button>
      </div>

      <div v-if="searchResults.length" class="search-results">
        Found {{ searchResults.length }} match(es) at offset(s): 
        <span 
          v-for="(offset, idx) in searchResults" 
          :key="idx"
          class="search-result-link"
          @click="goToOffset(offset)"
        >
          0x{{ offset.toString(16).toUpperCase().padStart(8, '0') }}
        </span>
      </div>

      <!-- Hex Grid -->
      <div v-if="viewMode === 'hex'" class="hex-grid-container">
        <div class="hex-grid">
          <div class="hex-header">
            <div class="offset-column">Offset</div>
            <div class="hex-columns">
              <span v-for="i in 16" :key="i" class="hex-header-col">
                {{ (i - 1).toString(16).toUpperCase() }}
              </span>
            </div>
            <div class="ascii-column">ASCII</div>
          </div>

          <div v-for="(row, idx) in displayRows" :key="idx" class="hex-row">
            <div class="offset-cell">{{ formatOffset(row.offset) }}</div>
            <div class="hex-bytes">
              <span 
                v-for="(byte, byteIdx) in row.bytes" 
                :key="byteIdx"
                class="hex-byte"
                :class="{ 
                  'highlight': isHighlighted(row.offset + byteIdx),
                  'null-byte': byte === '00'
                }"
                @click="selectByte(row.offset + byteIdx)"
              >
                {{ byte }}
              </span>
            </div>
            <div class="ascii-bytes">
              <span 
                v-for="(char, charIdx) in row.ascii" 
                :key="charIdx"
                class="ascii-char"
                :class="{ 'highlight': isHighlighted(row.offset + charIdx) }"
              >
                {{ char }}
              </span>
            </div>
          </div>
        </div>
      </div>

      <!-- Pagination -->
      <div v-if="viewMode === 'hex'" class="pagination">
        <button @click="prevPage" :disabled="currentOffset === 0" class="btn btn-secondary">
          ← Previous
        </button>
        <span class="page-info">
          Page {{ currentPage }} of {{ totalPages }}
        </span>
        <button @click="nextPage" :disabled="currentOffset + bytesPerPage >= fileData.size" class="btn btn-secondary">
          Next →
        </button>
      </div>

      <!-- Actions -->
      <div class="actions">
        <button v-if="viewMode === 'hex'" @click="downloadAsText" class="btn btn-info">📄 Export Hex as Text</button>
        <button v-if="viewMode === 'text'" @click="downloadTextContent" class="btn btn-info">💾 Download Text</button>
      </div>
    </section>

    <!-- Error Display -->
    <div v-if="error" class="error-message">
      <h3>❌ Error</h3>
      <p>{{ error }}</p>
    </div>
  </div>
</template>

<script>
import axios from 'axios';

export default {
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
        const response = await axios.post('http://localhost:5000/api/hex/upload', formData, {
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
          this.error = response.data.message || 'Failed to load file';
        }
      } catch (err) {
        this.error = err.response?.data?.message || err.message || 'Failed to upload file';
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
.hex-viewer-container {
  max-width: 1400px;
  margin: 0 auto;
}

.subtitle {
  color: #666;
  margin-bottom: 2rem;
}

.upload-section {
  margin-bottom: 2rem;
}

.upload-box {
  border: 3px dashed #667eea;
  border-radius: 12px;
  padding: 3rem;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s;
  background: #f8f9ff;
}

.upload-box:hover {
  background: #e8e9ff;
  border-color: #764ba2;
}

.upload-icon {
  font-size: 4rem;
  margin-bottom: 1rem;
}

.file-formats {
  color: #999;
  font-size: 0.9rem;
}

.progress-section {
  margin-top: 1rem;
}

.progress-bar {
  height: 8px;
  background: #eee;
  border-radius: 4px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #667eea, #764ba2);
  transition: width 0.3s;
}

.file-info {
  background: #f8f9ff;
  padding: 1rem;
  border-radius: 8px;
  margin-bottom: 1rem;
  border: 2px solid #667eea;
}

.info-row {
  margin: 0.5rem 0;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.btn-close {
  background: #e74c3c;
  color: white;
  border: none;
  padding: 0.4rem 0.8rem;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 600;
}

.search-section {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 1rem;
}

.search-input {
  flex: 1;
  padding: 0.6rem;
  border: 2px solid #667eea;
  border-radius: 6px;
  font-family: 'Courier New', monospace;
}

.search-results {
  background: #e9f8ef;
  padding: 0.75rem;
  border-radius: 6px;
  margin-bottom: 1rem;
  border: 1px solid #27ae60;
}

.search-result-link {
  display: inline-block;
  margin: 0 0.5rem;
  color: #667eea;
  cursor: pointer;
  font-weight: 600;
}

.search-result-link:hover {
  text-decoration: underline;
}

.hex-grid-container {
  background: white;
  border: 2px solid #667eea;
  border-radius: 8px;
  padding: 1rem;
  margin-bottom: 1rem;
  overflow-x: auto;
}

.hex-grid {
  font-family: 'Courier New', monospace;
  font-size: 0.9rem;
}

.hex-header {
  display: grid;
  grid-template-columns: 120px 1fr 180px;
  gap: 1rem;
  padding: 0.5rem 0;
  border-bottom: 2px solid #667eea;
  font-weight: 700;
  color: #667eea;
  margin-bottom: 0.5rem;
}

.hex-columns {
  display: grid;
  grid-template-columns: repeat(16, 1fr);
  gap: 0.25rem;
  text-align: center;
}

.hex-row {
  display: grid;
  grid-template-columns: 120px 1fr 180px;
  gap: 1rem;
  padding: 0.25rem 0;
  border-bottom: 1px solid #eee;
}

.hex-row:hover {
  background: #f8f9ff;
}

.offset-cell {
  color: #667eea;
  font-weight: 600;
}

.hex-bytes {
  display: grid;
  grid-template-columns: repeat(16, 1fr);
  gap: 0.25rem;
  text-align: center;
}

.hex-byte {
  padding: 0.1rem;
  cursor: pointer;
  border-radius: 2px;
}

.hex-byte:hover {
  background: #764ba2;
  color: white;
}

.hex-byte.highlight {
  background: #f39c12;
  color: white;
  font-weight: 700;
}

.hex-byte.null-byte {
  color: #bbb;
}

.ascii-bytes {
  display: grid;
  grid-template-columns: repeat(16, 1fr);
  text-align: center;
  color: #555;
}

.ascii-char.highlight {
  background: #f39c12;
  color: white;
  font-weight: 700;
}

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 1rem;
  margin: 1rem 0;
}

.page-info {
  font-weight: 600;
  color: #667eea;
}

.actions {
  display: flex;
  gap: 0.75rem;
  justify-content: center;
  margin-top: 1rem;
}

.btn {
  padding: 0.75rem 1.25rem;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 600;
  color: white;
  transition: all 0.3s;
}

.btn-primary {
  background: #667eea;
}

.btn-secondary {
  background: #95a5a6;
}

.btn-info {
  background: #16a085;
}

.btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.error-message {
  background: #fdecea;
  border: 2px solid #e74c3c;
  color: #c0392b;
  padding: 1rem;
  border-radius: 8px;
  margin-top: 1rem;
}

.view-toggle {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 1rem;
  justify-content: center;
}

.toggle-btn {
  padding: 0.75rem 1.5rem;
  border: 2px solid #667eea;
  background: white;
  color: #667eea;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 600;
  transition: all 0.3s;
}

.toggle-btn.active {
  background: #667eea;
  color: white;
}

.toggle-btn:hover:not(.active) {
  background: #f8f9ff;
}

.text-view {
  background: white;
  border: 2px solid #667eea;
  border-radius: 8px;
  margin-bottom: 1rem;
  overflow: hidden;
}

.text-header {
  background: #667eea;
  color: white;
  padding: 0.75rem 1rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 600;
}

.text-content {
  padding: 1.5rem;
  margin: 0;
  font-family: 'Courier New', monospace;
  font-size: 0.9rem;
  line-height: 1.6;
  max-height: 600px;
  overflow: auto;
  white-space: pre-wrap;
  word-wrap: break-word;
  background: #f8f9fa;
}

.text-content.format-json {
  color: #27ae60;
}

.text-content.format-xml {
  color: #e67e22;
}

.text-content.format-text {
  color: #2c3e50;
}

.badge {
  display: inline-block;
  padding: 0.25rem 0.75rem;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 700;
  text-transform: uppercase;
}

.badge-text {
  background: #3498db;
  color: white;
}

.badge-json {
  background: #27ae60;
  color: white;
}

.badge-xml {
  background: #e67e22;
  color: white;
}

.badge-binary {
  background: #95a5a6;
  color: white;
}

.encoding-info {
  font-size: 0.85rem;
  color: #7f8c8d;
  margin-left: 0.5rem;
}

.btn-sm {
  padding: 0.4rem 0.8rem;
  font-size: 0.85rem;
}
</style>

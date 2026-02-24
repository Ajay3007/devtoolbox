<template>
  <div class="pcap-merger-container">
    <h1>PCAP Merger</h1>
    <p class="subtitle">Merge two or more PCAP/PCAPNG files into a single capture</p>

    <section class="form-section">
      <h2>Input Files</h2>
      <div class="upload-row">
        <label class="file-input-label" for="pcapFiles">Select PCAP/PCAPNG files (min 2)</label>
        <input
          id="pcapFiles"
          type="file"
          multiple
          accept=".pcap,.pcapng"
          @change="handleFileSelect"
        />
      </div>

      <div v-if="selectedFiles.length" class="file-list">
        <div v-for="(file, index) in selectedFiles" :key="file.name + index" class="file-item">
          <div>
            <strong>{{ file.name }}</strong>
            <span class="meta">{{ formatBytes(file.size) }}</span>
          </div>
          <button class="btn-icon" @click="removeFile(index)">✕</button>
        </div>
      </div>

      <div class="output-name">
        <label for="outputName">Output filename (optional)</label>
        <input
          id="outputName"
          type="text"
          v-model="outputName"
          placeholder="merged_output.pcap"
        />
      </div>

      <div class="actions">
        <button class="btn btn-primary" :disabled="merging || !canMerge" @click="mergeFiles">
          <span v-if="merging">⏳ Merging...</span>
          <span v-else>🔀 Merge PCAPs</span>
        </button>
        <button class="btn btn-secondary" :disabled="merging" @click="resetForm">Reset</button>
      </div>
    </section>

    <section v-if="result" class="result success">
      <h3>✅ Merge Successful</h3>
      <p><strong>File:</strong> {{ result.filepath }}</p>
      <p><strong>Packets:</strong> {{ result.packet_count }}</p>
      <p><strong>Source files:</strong> {{ result.source_files.join(', ') }}</p>
      <div class="actions">
        <button class="btn btn-success" @click="openInEditor">📝 Open in Editor</button>
        <button class="btn btn-info" @click="downloadFile">💾 Download</button>
      </div>
    </section>

    <section v-if="error" class="result error">
      <h3>❌ Error</h3>
      <p>{{ error }}</p>
    </section>
  </div>
</template>

<script>
import axios from 'axios';

export default {
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
    canMerge() {
      return this.selectedFiles.length >= 2;
    }
  },
  methods: {
    handleFileSelect(event) {
      this.error = null;
      const files = Array.from(event.target.files || []);
      this.selectedFiles = files;
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
          this.result = response.data;
        } else {
          this.error = response.data.message || 'Failed to merge files';
        }
      } catch (err) {
        this.error = err.response?.data?.message || err.message || 'Failed to merge files';
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
.pcap-merger-container {
  max-width: 900px;
  margin: 0 auto;
  background: #fff;
  padding: 2rem;
  border-radius: 12px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.08);
}

.subtitle {
  color: #555;
  margin-bottom: 1.5rem;
}

.form-section {
  margin-bottom: 1.5rem;
}

.upload-row {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  margin-bottom: 1rem;
}

.file-input-label {
  font-weight: 600;
  color: #333;
}

.file-list {
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  padding: 0.75rem;
  margin-bottom: 1rem;
  background: #fafafa;
}

.file-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.5rem 0;
  border-bottom: 1px solid #eee;
}

.file-item:last-child {
  border-bottom: none;
}

.meta {
  color: #666;
  margin-left: 0.5rem;
  font-size: 0.9rem;
}

.btn-icon {
  background: none;
  border: none;
  color: #c0392b;
  cursor: pointer;
  font-size: 1rem;
}

.output-name {
  margin: 1rem 0;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.output-name input {
  padding: 0.6rem 0.75rem;
  border: 1px solid #ddd;
  border-radius: 8px;
}

.actions {
  display: flex;
  gap: 0.75rem;
  margin-top: 0.5rem;
  flex-wrap: wrap;
}

.btn {
  padding: 0.75rem 1.25rem;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 600;
  color: white;
}

.btn-primary {
  background: #667eea;
}

.btn-secondary {
  background: #95a5a6;
}

.btn-success {
  background: #27ae60;
}

.btn-info {
  background: #16a085;
}

.result {
  padding: 1.25rem;
  border-radius: 10px;
  margin-top: 1rem;
}

.success {
  background: #e9f8ef;
  border: 1px solid #c8e6c9;
}

.error {
  background: #fdecea;
  border: 1px solid #f5c6cb;
  color: #c0392b;
}
</style>

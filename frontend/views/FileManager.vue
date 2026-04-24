<template>
  <div class="file-manager-container">
    <h1>📂 File Manager</h1>
    <p class="subtitle">View, rename, and delete files in the uploads folder</p>

    <!-- Toolbar -->
    <div class="toolbar">
      <button @click="loadFiles" class="btn btn-secondary" :disabled="loading">
        🔄 Refresh
      </button>
      <span class="file-count" v-if="!loading">{{ files.length }} file(s)</span>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="state-box">
      <span class="spinner">⏳</span> Loading files…
    </div>

    <!-- Empty -->
    <div v-else-if="files.length === 0" class="state-box empty">
      <div class="empty-icon">📭</div>
      <p>No files found in the uploads folder.</p>
    </div>

    <!-- File Table -->
    <div v-else class="table-wrapper">
      <table class="file-table">
        <thead>
          <tr>
            <th>Filename</th>
            <th>Type</th>
            <th>Size</th>
            <th>Last Modified</th>
            <th class="actions-col">Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="file in files" :key="file.name" :class="{ renaming: renamingFile === file.name }">
            <td class="filename-cell">
              <span v-if="renamingFile !== file.name" class="filename">{{ file.name }}</span>
              <div v-else class="rename-inline">
                <input
                  v-model="renameValue"
                  class="rename-input"
                  @keyup.enter="confirmRename(file.name)"
                  @keyup.esc="cancelRename"
                  ref="renameInput"
                />
                <button @click="confirmRename(file.name)" class="btn-icon btn-success-icon" title="Save">✓</button>
                <button @click="cancelRename" class="btn-icon btn-danger-icon" title="Cancel">✕</button>
              </div>
            </td>
            <td>
              <span class="badge" :class="'ext-' + file.extension">
                {{ file.extension || 'file' }}
              </span>
            </td>
            <td class="size-cell">{{ formatBytes(file.size) }}</td>
            <td class="date-cell">{{ formatDate(file.modified) }}</td>
            <td class="actions-cell">
              <button @click="downloadFile(file.name)" class="btn-icon" title="Download">💾</button>
              <button @click="openInEditor(file.name)" v-if="isPcap(file)" class="btn-icon" title="Open in PCAP Editor">📝</button>
              <button @click="openHexViewer(file.name)" class="btn-icon" title="Open in Hex Viewer">🔢</button>
              <button @click="startRename(file)" class="btn-icon" title="Rename" :disabled="renamingFile !== null">✏️</button>
              <button @click="confirmDelete(file.name)" class="btn-icon btn-danger-icon" title="Delete">🗑️</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Error -->
    <div v-if="error" class="error-msg">❌ {{ error }}</div>

    <!-- Success Toast -->
    <transition name="toast">
      <div v-if="toast" class="toast">{{ toast }}</div>
    </transition>

    <!-- Delete Confirm Modal -->
    <div v-if="deleteTarget" class="modal-overlay" @click.self="deleteTarget = null">
      <div class="modal">
        <div class="modal-header">
          <h3>🗑️ Delete File</h3>
        </div>
        <div class="modal-body">
          <p>Are you sure you want to permanently delete <strong>{{ deleteTarget }}</strong>?</p>
          <p class="warn-text">This action cannot be undone.</p>
        </div>
        <div class="modal-footer">
          <button @click="deleteTarget = null" class="btn btn-cancel">Cancel</button>
          <button @click="doDelete" class="btn btn-danger" :disabled="deleting">
            {{ deleting ? 'Deleting…' : 'Delete' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'FileManager',
  data() {
    return {
      files: [],
      loading: false,
      error: null,
      toast: null,
      renamingFile: null,
      renameValue: '',
      deleteTarget: null,
      deleting: false,
    };
  },
  mounted() {
    this.loadFiles();
  },
  methods: {
    async loadFiles() {
      this.loading = true;
      this.error = null;
      try {
        const res = await this.$axios.get('/files');
        if (res.data.success) {
          this.files = res.data.files;
        } else {
          this.error = 'Failed to load files';
        }
      } catch (err) {
        this.error = err.message || 'Failed to load files';
      } finally {
        this.loading = false;
      }
    },

    startRename(file) {
      this.renamingFile = file.name;
      this.renameValue = file.name;
      this.$nextTick(() => {
        const input = this.$refs.renameInput;
        if (input) (Array.isArray(input) ? input[0] : input).focus();
      });
    },

    cancelRename() {
      this.renamingFile = null;
      this.renameValue = '';
    },

    async confirmRename(oldName) {
      if (!this.renameValue.trim() || this.renameValue === oldName) {
        this.cancelRename();
        return;
      }
      try {
        const res = await this.$axios.put(`/files/${encodeURIComponent(oldName)}/rename`, {
          new_name: this.renameValue.trim()
        });
        if (res.data.success) {
          this.showToast(`Renamed to ${res.data.new_name}`);
          this.cancelRename();
          await this.loadFiles();
        } else {
          this.error = res.data.message || 'Rename failed';
        }
      } catch (err) {
        this.error = err.response?.data?.message || err.message || 'Rename failed';
      }
    },

    confirmDelete(filename) {
      this.deleteTarget = filename;
    },

    async doDelete() {
      if (!this.deleteTarget) return;
      this.deleting = true;
      try {
        const res = await this.$axios.delete(`/files/${encodeURIComponent(this.deleteTarget)}`);
        if (res.data.success) {
          this.showToast(`Deleted ${this.deleteTarget}`);
          this.deleteTarget = null;
          await this.loadFiles();
        } else {
          this.error = res.data.message || 'Delete failed';
        }
      } catch (err) {
        this.error = err.response?.data?.message || err.message || 'Delete failed';
      } finally {
        this.deleting = false;
      }
    },

    async downloadFile(filename) {
      try {
        const res = await this.$axios.get(`/pcap/export/uploads/${encodeURIComponent(filename)}`, {
          responseType: 'blob'
        });
        const url = window.URL.createObjectURL(new Blob([res.data]));
        const link = document.createElement('a');
        link.href = url;
        link.setAttribute('download', filename);
        document.body.appendChild(link);
        link.click();
        link.remove();
        window.URL.revokeObjectURL(url);
      } catch {
        this.error = 'Download failed';
      }
    },

    openInEditor(filename) {
      this.$router.push({ name: 'pcap-editor', query: { file: `uploads/${filename}` } });
    },

    openHexViewer() {
      this.$router.push({ name: 'hex-viewer' });
    },

    isPcap(file) {
      return ['pcap', 'pcapng'].includes(file.extension);
    },

    showToast(msg) {
      this.toast = msg;
      setTimeout(() => { this.toast = null; }, 3000);
    },

    formatBytes(bytes) {
      if (!bytes) return '0 B';
      const sizes = ['B', 'KB', 'MB', 'GB'];
      const i = Math.min(Math.floor(Math.log(bytes) / Math.log(1024)), sizes.length - 1);
      return `${(bytes / Math.pow(1024, i)).toFixed(1)} ${sizes[i]}`;
    },

    formatDate(iso) {
      if (!iso) return '—';
      return new Date(iso).toLocaleString();
    },
  }
};
</script>

<style scoped>
.file-manager-container {
  max-width: 1100px;
  margin: 0 auto;
  animation: fadeIn 0.4s ease;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(8px); }
  to   { opacity: 1; transform: translateY(0); }
}

h1 { font-size: 2rem; color: #333; margin-bottom: 0.25rem; }

.subtitle { color: #666; margin-bottom: 1.5rem; }

.toolbar {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 1.25rem;
}

.file-count { color: #888; font-size: 0.9rem; }

.state-box {
  text-align: center;
  padding: 3rem;
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.07);
  color: #999;
}

.empty-icon { font-size: 3rem; margin-bottom: 1rem; }

.table-wrapper {
  background: white;
  border-radius: 12px;
  box-shadow: 0 4px 16px rgba(0,0,0,0.08);
  overflow: hidden;
}

.file-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.93rem;
}

.file-table thead tr {
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: white;
}

.file-table th {
  padding: 0.9rem 1.1rem;
  text-align: left;
  font-weight: 600;
  white-space: nowrap;
}

.file-table td {
  padding: 0.75rem 1.1rem;
  border-bottom: 1px solid #f0f0f0;
  vertical-align: middle;
}

.file-table tbody tr:hover { background: #f8f9ff; }
.file-table tbody tr.renaming { background: #fff8e1; }
.file-table tbody tr:last-child td { border-bottom: none; }

.filename { font-family: 'Courier New', monospace; word-break: break-all; }

.rename-inline {
  display: flex;
  align-items: center;
  gap: 0.4rem;
}

.rename-input {
  flex: 1;
  padding: 0.4rem 0.6rem;
  border: 2px solid #667eea;
  border-radius: 6px;
  font-family: 'Courier New', monospace;
  font-size: 0.9rem;
  outline: none;
}

.badge {
  display: inline-block;
  padding: 0.2rem 0.6rem;
  border-radius: 10px;
  font-size: 0.75rem;
  font-weight: 700;
  text-transform: uppercase;
  background: #e0e0e0;
  color: #555;
}

.ext-pcap, .ext-pcapng { background: #667eea; color: white; }
.ext-txt, .ext-log      { background: #27ae60; color: white; }
.ext-json               { background: #f39c12; color: white; }

.size-cell, .date-cell { color: #666; white-space: nowrap; }

.actions-col { width: 1%; white-space: nowrap; }
.actions-cell { display: flex; gap: 0.35rem; }

.btn-icon {
  background: none;
  border: 1px solid #ddd;
  border-radius: 6px;
  padding: 0.35rem 0.5rem;
  cursor: pointer;
  font-size: 1rem;
  transition: background 0.2s, transform 0.15s;
}

.btn-icon:hover:not(:disabled) { background: #f0f4ff; transform: translateY(-1px); }
.btn-icon:disabled { opacity: 0.4; cursor: not-allowed; }

.btn-success-icon { color: #27ae60; border-color: #27ae60; }
.btn-danger-icon  { color: #e74c3c; border-color: #e74c3c; }

/* Buttons */
.btn {
  padding: 0.65rem 1.3rem;
  border: none;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.25s;
}

.btn-secondary { background: #95a5a6; color: white; }
.btn-secondary:hover { background: #7f8c8d; }

.btn-cancel { background: #ecf0f1; color: #333; }
.btn-cancel:hover { background: #dde1e5; }

.btn-danger { background: #e74c3c; color: white; }
.btn-danger:hover:not(:disabled) { background: #c0392b; }
.btn-danger:disabled { opacity: 0.6; cursor: not-allowed; }

.error-msg {
  background: #fdecea;
  border: 1px solid #e74c3c;
  color: #c0392b;
  padding: 0.85rem 1.1rem;
  border-radius: 8px;
  margin-top: 1rem;
}

/* Modal */
.modal-overlay {
  position: fixed; inset: 0;
  background: rgba(0,0,0,0.45);
  display: flex; align-items: center; justify-content: center;
  z-index: 1000;
}

.modal {
  background: white;
  border-radius: 12px;
  width: 90%;
  max-width: 460px;
  box-shadow: 0 16px 48px rgba(0,0,0,0.25);
}

.modal-header {
  padding: 1.2rem 1.5rem;
  border-bottom: 1px solid #eee;
}

.modal-header h3 { margin: 0; }

.modal-body {
  padding: 1.25rem 1.5rem;
}

.warn-text { color: #c0392b; font-size: 0.9rem; margin-top: 0.5rem; }

.modal-footer {
  display: flex;
  gap: 0.75rem;
  justify-content: flex-end;
  padding: 1rem 1.5rem;
  border-top: 1px solid #eee;
}

/* Toast */
.toast {
  position: fixed;
  bottom: 2rem;
  right: 2rem;
  background: #2ecc71;
  color: white;
  padding: 0.85rem 1.4rem;
  border-radius: 10px;
  font-weight: 600;
  box-shadow: 0 6px 20px rgba(46,204,113,0.4);
  z-index: 2000;
}

.toast-enter-active, .toast-leave-active { transition: all 0.3s ease; }
.toast-enter-from, .toast-leave-to { opacity: 0; transform: translateY(1rem); }

@media (max-width: 768px) {
  .file-table th:nth-child(4),
  .file-table td:nth-child(4) { display: none; }
  h1 { font-size: 1.5rem; }
}
</style>

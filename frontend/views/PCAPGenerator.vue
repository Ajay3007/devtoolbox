<template>
  <div class="pcap-generator">
    <h1>PCAP Generator</h1>
    <p class="subtitle">Generate PCAP files with various protocols and configurations</p>

    <div class="generator-container">
      <!-- Protocol Selection -->
      <div class="form-section">
        <h2>Protocol Configuration</h2>
        
        <div class="form-group">
          <label for="protocol">Protocol *</label>
          <select id="protocol" v-model="config.protocol" class="form-control">
            <option value="tcp">TCP</option>
            <option value="http">HTTP</option>
            <option value="udp">UDP</option>
            <option value="dns_udp">DNS Query over UDP</option>
            <option value="dns_tcp">DNS Query over TCP</option>
            <option value="tls">TLS (HTTPS)</option>
            <option value="icmp">ICMP (Ping)</option>
            <option value="arp">ARP (Who-Has)</option>
          </select>
        </div>

        <div class="form-group">
          <label for="packetCount">Number of Packets *</label>
          <input 
            type="number" 
            id="packetCount" 
            v-model.number="config.packet_count" 
            class="form-control"
            min="1"
            max="1000"
            placeholder="Enter packet count (1-1000)"
          />
        </div>
      </div>

      <!-- ── Import from existing PCAP ── -->
      <div class="form-section import-section">
        <div class="import-header" @click="importPanel.open = !importPanel.open">
          <span>📂 Import field values from existing PCAP <em>(optional)</em></span>
          <span class="chevron">{{ importPanel.open ? '▲' : '▼' }}</span>
        </div>

        <div v-if="importPanel.open" class="import-body">
          <div class="import-file-row">
            <!-- Dropdown of uploaded files -->
            <select v-model="importPanel.selectedFile" class="form-control import-select"
                    :disabled="importPanel.loading">
              <option value="">— select an uploaded file —</option>
              <option v-for="f in importPanel.fileList" :key="f.name" :value="f.name">
                {{ f.name }} ({{ formatBytes(f.size) }})
              </option>
            </select>

            <button @click="extractFieldValues"
                    class="btn btn-import"
                    :disabled="!importPanel.selectedFile || importPanel.loading">
              {{ importPanel.loading ? '⏳ Reading…' : '🔍 Extract Values' }}
            </button>

            <button @click="loadFileList" class="btn btn-refresh-files" title="Refresh file list">
              🔄
            </button>
          </div>

          <p v-if="importPanel.error" class="import-error">❌ {{ importPanel.error }}</p>

          <div v-if="importPanel.values" class="import-summary">
            📊 Extracted from <strong>{{ importPanel.packetCount }}</strong> packets.
            Use the <strong>↩ pick</strong> dropdowns next to each field below.
          </div>
        </div>
      </div>

      <!-- Network Configuration -->
      <div class="form-section">
        <h2>Network Configuration</h2>

        <div class="form-row">
          <div class="form-group">
            <label for="srcMac">Source MAC Address</label>
            <div class="field-with-picker">
              <input type="text" id="srcMac" v-model="config.options.src_mac"
                     class="form-control" placeholder="00:0c:29:63:c0:fb" />
              <select v-if="hasPicks('src_mac')" class="picker-select"
                      @change="applyPick('src_mac', $event.target.value); $event.target.value=''">
                <option value="">↩ pick</option>
                <option v-for="v in importPanel.values.src_mac" :key="v" :value="v">{{ v }}</option>
              </select>
            </div>
          </div>

          <div class="form-group">
            <label for="dstMac">Destination MAC Address</label>
            <div class="field-with-picker">
              <input type="text" id="dstMac" v-model="config.options.dst_mac"
                     class="form-control" placeholder="00:0c:29:63:c0:fa" />
              <select v-if="hasPicks('dst_mac')" class="picker-select"
                      @change="applyPick('dst_mac', $event.target.value); $event.target.value=''">
                <option value="">↩ pick</option>
                <option v-for="v in importPanel.values.dst_mac" :key="v" :value="v">{{ v }}</option>
              </select>
            </div>
          </div>
        </div>

        <div class="form-row">
          <div class="form-group">
            <label for="srcIp">Source IP Address <small>(IPv4 or IPv6)</small></label>
            <div class="field-with-picker">
              <input type="text" id="srcIp" v-model="config.options.src_ip"
                     class="form-control" placeholder="192.168.1.100" />
              <select v-if="hasPicks('src_ip')" class="picker-select"
                      @change="applyPick('src_ip', $event.target.value); $event.target.value=''">
                <option value="">↩ pick</option>
                <option v-for="v in importPanel.values.src_ip" :key="v" :value="v">{{ v }}</option>
              </select>
            </div>
          </div>

          <div class="form-group">
            <label for="dstIp">Destination IP Address <small>(IPv4 or IPv6)</small></label>
            <div class="field-with-picker">
              <input type="text" id="dstIp" v-model="config.options.dst_ip"
                     class="form-control" placeholder="192.168.1.200" />
              <select v-if="hasPicks('dst_ip')" class="picker-select"
                      @change="applyPick('dst_ip', $event.target.value); $event.target.value=''">
                <option value="">↩ pick</option>
                <option v-for="v in importPanel.values.dst_ip" :key="v" :value="v">{{ v }}</option>
              </select>
            </div>
          </div>
        </div>

        <div class="form-row">
          <div class="form-group">
            <label for="srcPort">Source Port</label>
            <div class="field-with-picker">
              <input type="number" id="srcPort" v-model.number="config.options.src_port"
                     class="form-control" min="1" max="65535" placeholder="49152" />
              <select v-if="hasPicks('src_port')" class="picker-select"
                      @change="applyPick('src_port', +$event.target.value); $event.target.value=''">
                <option value="">↩ pick</option>
                <option v-for="v in importPanel.values.src_port" :key="v" :value="v">{{ v }}</option>
              </select>
            </div>
          </div>

          <div class="form-group">
            <label for="dstPort">Destination Port</label>
            <div class="field-with-picker">
              <input type="number" id="dstPort" v-model.number="config.options.dst_port"
                     class="form-control" min="1" max="65535" placeholder="80" />
              <select v-if="hasPicks('dst_port')" class="picker-select"
                      @change="applyPick('dst_port', +$event.target.value); $event.target.value=''">
                <option value="">↩ pick</option>
                <option v-for="v in importPanel.values.dst_port" :key="v" :value="v">{{ v }}</option>
              </select>
            </div>
          </div>
        </div>

        <!-- VLAN picker (shown even when VLAN toggle is off) -->
        <div class="form-row" v-if="hasPicks('vlan_id') || config.use_vlan">
          <div class="form-group">
            <label>
              <input type="checkbox" v-model="config.use_vlan" />
              <span>Add VLAN Tag</span>
            </label>
          </div>
          <div class="form-group" v-if="config.use_vlan || hasPicks('vlan_id')">
            <label for="vlanId">VLAN ID</label>
            <div class="field-with-picker">
              <input type="number" id="vlanId" v-model.number="config.vlan_id"
                     class="form-control" min="1" max="4094" placeholder="1-4094"
                     :disabled="!config.use_vlan" />
              <select v-if="hasPicks('vlan_id')" class="picker-select"
                      @change="applyPick('vlan_id', +$event.target.value); config.use_vlan = true; $event.target.value=''">
                <option value="">↩ pick</option>
                <option v-for="v in importPanel.values.vlan_id" :key="v" :value="v">{{ v }}</option>
              </select>
            </div>
          </div>
        </div>
      </div>

      <!-- Protocol-specific Options -->
      <div class="form-section" v-if="showProtocolOptions">
        <h2>Protocol-Specific Options</h2>
        
        <div class="form-group" v-if="config.protocol === 'http'">
          <label for="httpHost">HTTP Host Header</label>
          <input 
            type="text" 
            id="httpHost" 
            v-model="config.options.http_host" 
            class="form-control"
            placeholder="example.com"
          />
        </div>

        <div class="form-group" v-if="config.protocol === 'dns_udp' || config.protocol === 'dns_tcp'">
          <label for="dnsQuery">DNS Query Domain</label>
          <input 
            type="text" 
            id="dnsQuery" 
            v-model="config.options.dns_query" 
            class="form-control"
            placeholder="example.com"
          />
        </div>

        <div class="form-group" v-if="config.protocol === 'tls'">
          <label for="tlsSni">TLS SNI (Server Name)</label>
          <input 
            type="text" 
            id="tlsSni" 
            v-model="config.options.tls_sni" 
            class="form-control"
            placeholder="example.com"
          />
        </div>

        <div class="form-group" v-if="config.protocol === 'icmp'">
          <label for="icmpPayload">ICMP Payload (optional, max 56 chars)</label>
          <input 
            type="text" 
            id="icmpPayload" 
            v-model="config.options.icmp_payload" 
            class="form-control"
            placeholder="DevToolBox ICMP"
            maxlength="56"
          />
        </div>

        <div class="form-group" v-if="config.protocol === 'arp'">
          <label for="targetIp">Target IP (Who-Has?)</label>
          <input 
            type="text" 
            id="targetIp" 
            v-model="config.options.target_ip" 
            class="form-control"
            placeholder="192.168.1.200"
          />
        </div>
      </div>

      <!-- Action Buttons -->
      <div class="action-section">
        <button 
          @click="generatePCAP" 
          :disabled="generating || !isValid"
          class="btn btn-primary btn-large"
        >
          <span v-if="generating">⏳ Generating...</span>
          <span v-else>🔧 Generate PCAP</span>
        </button>

        <button 
          @click="resetForm" 
          class="btn btn-secondary btn-large"
          :disabled="generating"
        >
          🔄 Reset
        </button>
      </div>

      <!-- Success Message -->
      <div v-if="generatedFile" class="success-message">
        <h3>✅ PCAP Generated Successfully!</h3>
        <p><strong>File:</strong> {{ generatedFile.filepath }}</p>
        <p><strong>Packets:</strong> {{ generatedFile.packet_count }}</p>
        <p><strong>Protocol:</strong> {{ generatedFile.protocol.toUpperCase() }}</p>
        <p v-if="generatedFile.vlan_id"><strong>VLAN:</strong> {{ generatedFile.vlan_id }}</p>
        
        <div class="action-buttons">
          <button @click="openInEditor" class="btn btn-success">
            📝 Open in Editor
          </button>
          <button @click="downloadFile" class="btn btn-info">
            💾 Download
          </button>
        </div>
      </div>

      <!-- Error Message -->
      <div v-if="error" class="error-message">
        <h3>❌ Error</h3>
        <p>{{ error }}</p>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios';

export default {
  name: 'PCAPGenerator',
  data() {
    return {
      config: {
        protocol: 'tcp',
        packet_count: 10,
        use_vlan: false,
        vlan_id: 100,
        options: {
          src_mac: '00:0c:29:63:c0:fb',
          dst_mac: '00:0c:29:63:c0:fa',
          src_ip: '192.168.1.100',
          dst_ip: '192.168.1.200',
          src_port: null,
          dst_port: 80,
          http_host: 'example.com',
          dns_query: 'example.com',
          tls_sni: 'example.com',
          icmp_payload: 'DevToolBox ICMP',
          target_ip: '192.168.1.200'
        }
      },
      generating: false,
      generatedFile: null,
      error: null,
      // Import-from-PCAP state
      importPanel: {
        open: false,
        fileList: [],
        selectedFile: '',
        loading: false,
        error: null,
        values: null,   // { src_mac:[], dst_mac:[], ... }
        packetCount: 0
      }
    };
  },
  mounted() {
    this.loadFileList();
  },
  computed: {
    isValid() {
      return this.config.protocol && 
             this.config.packet_count >= 1 && 
             this.config.packet_count <= 1000;
    },
    showProtocolOptions() {
      return ['http', 'dns_udp', 'dns_tcp', 'tls', 'icmp', 'arp'].includes(this.config.protocol);
    }
  },
  methods: {
    // ── Import helpers ──
    async loadFileList() {
      try {
        const res = await this.$axios.get('/files');
        if (res.data.success) {
          this.importPanel.fileList = (res.data.files || []).filter(
            f => ['pcap', 'pcapng'].includes(f.extension)
          );
        }
      } catch { /* silently ignore */ }
    },

    async extractFieldValues() {
      if (!this.importPanel.selectedFile) return;
      this.importPanel.loading = true;
      this.importPanel.error = null;
      this.importPanel.values = null;
      try {
        const res = await this.$axios.get(
          `/pcap/field-values/uploads/${encodeURIComponent(this.importPanel.selectedFile)}`
        );
        if (res.data.success) {
          this.importPanel.values = res.data.data.fields;
          this.importPanel.packetCount = res.data.data.packet_count;
        } else {
          this.importPanel.error = res.data.message || 'Extraction failed';
        }
      } catch (err) {
        this.importPanel.error = err.response?.data?.message || err.message || 'Request failed';
      } finally {
        this.importPanel.loading = false;
      }
    },

    hasPicks(field) {
      return this.importPanel.values &&
             Array.isArray(this.importPanel.values[field]) &&
             this.importPanel.values[field].length > 0;
    },

    applyPick(field, value) {
      if (!value && value !== 0) return;
      // VLAN is on config root; everything else is config.options
      if (field === 'vlan_id') {
        this.config.vlan_id = value;
        this.config.use_vlan = true;
      } else {
        this.config.options[field] = value;
      }
    },

    formatBytes(bytes) {
      if (!bytes) return '0 B';
      const s = ['B', 'KB', 'MB', 'GB'];
      const i = Math.min(Math.floor(Math.log(bytes) / Math.log(1024)), s.length - 1);
      return `${(bytes / Math.pow(1024, i)).toFixed(1)} ${s[i]}`;
    },

    // ── Original methods ──
    async generatePCAP() {
      this.generating = true;
      this.error = null;
      this.generatedFile = null;

      try {
        const payload = {
          protocol: this.config.protocol,
          packet_count: this.config.packet_count,
          options: { ...this.config.options }
        };

        // Add VLAN if enabled
        if (this.config.use_vlan) {
          payload.vlan_id = this.config.vlan_id;
        }

        // Clean up null values
        Object.keys(payload.options).forEach(key => {
          if (payload.options[key] === null || payload.options[key] === '') {
            delete payload.options[key];
          }
        });

        const response = await this.$axios.post('/pcap/generate', payload);

        if (response.data.success) {
          this.generatedFile = response.data;
        } else {
          this.error = response.data.message || 'Failed to generate PCAP';
        }
      } catch (err) {
        this.error = err.response?.data?.message || err.message || 'Failed to generate PCAP';
      } finally {
        this.generating = false;
      }
    },

    resetForm() {
      this.config = {
        protocol: 'tcp',
        packet_count: 10,
        use_vlan: false,
        vlan_id: 100,
        options: {
          src_mac: '00:0c:29:63:c0:fb',
          dst_mac: '00:0c:29:63:c0:fa',
          src_ip: '192.168.1.100',
          dst_ip: '192.168.1.200',
          src_port: null,
          dst_port: 80,
          http_host: 'example.com',
          dns_query: 'example.com',
          tls_sni: 'example.com'
        }
      };
      this.generatedFile = null;
      this.error = null;
    },

    openInEditor() {
      if (this.generatedFile) {
        this.$router.push({
          name: 'pcap-editor',
          query: { file: this.generatedFile.filepath }
        });
      }
    },

    async downloadFile() {
      if (this.generatedFile) {
        try {
          const response = await this.$axios.get(
            `/pcap/export/${encodeURIComponent(this.generatedFile.filepath)}`,
            { responseType: 'blob' }
          );

          const url = window.URL.createObjectURL(new Blob([response.data]));
          const link = document.createElement('a');
          link.href = url;
          link.setAttribute('download', this.generatedFile.filepath);
          document.body.appendChild(link);
          link.click();
          link.remove();
          window.URL.revokeObjectURL(url);
        } catch (err) {
          this.error = 'Failed to download file';
        }
      }
    }
  }
};
</script>

<style scoped>
.pcap-generator {
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem;
}

h1 {
  color: #2c3e50;
  margin-bottom: 0.5rem;
}

.subtitle {
  color: #7f8c8d;
  margin-bottom: 2rem;
}

.generator-container {
  background: white;
  border-radius: 8px;
  padding: 2rem;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
}

.form-section {
  margin-bottom: 2rem;
  padding-bottom: 2rem;
  border-bottom: 1px solid #ecf0f1;
}

.form-section:last-of-type {
  border-bottom: none;
}

.form-section h2 {
  color: #34495e;
  font-size: 1.25rem;
  margin-bottom: 1.5rem;
}

.form-group {
  margin-bottom: 1.5rem;
}

.form-group label {
  display: block;
  margin-bottom: 0.5rem;
  color: #2c3e50;
  font-weight: 500;
}

.form-control {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #bdc3c7;
  border-radius: 4px;
  font-size: 1rem;
  transition: border-color 0.3s;
}

.form-control:focus {
  outline: none;
  border-color: #3498db;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
}

.checkbox-group label {
  display: flex;
  align-items: center;
  cursor: pointer;
}

.checkbox-group input[type="checkbox"] {
  margin-right: 0.5rem;
  width: 1.2rem;
  height: 1.2rem;
  cursor: pointer;
}

.checkbox-group span {
  font-weight: 500;
}

.action-section {
  display: flex;
  gap: 1rem;
  margin-top: 2rem;
}

.btn {
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 4px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-large {
  padding: 1rem 2rem;
  font-size: 1.1rem;
}

.btn-primary {
  background: #3498db;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: #2980b9;
}

.btn-secondary {
  background: #95a5a6;
  color: white;
}

.btn-secondary:hover:not(:disabled) {
  background: #7f8c8d;
}

.btn-success {
  background: #27ae60;
  color: white;
}

.btn-success:hover {
  background: #229954;
}

.btn-info {
  background: #16a085;
  color: white;
}

.btn-info:hover {
  background: #138d75;
}

.success-message {
  margin-top: 2rem;
  padding: 1.5rem;
  background: #d5f4e6;
  border: 2px solid #27ae60;
  border-radius: 8px;
}

.success-message h3 {
  color: #27ae60;
  margin-bottom: 1rem;
}

.success-message p {
  margin: 0.5rem 0;
  color: #2c3e50;
}

.action-buttons {
  display: flex;
  gap: 1rem;
  margin-top: 1rem;
}

.error-message {
  margin-top: 2rem;
  padding: 1.5rem;
  background: #fadbd8;
  border: 2px solid #e74c3c;
  border-radius: 8px;
}

.error-message h3 {
  color: #e74c3c;
  margin-bottom: 1rem;
}

.error-message p {
  color: #c0392b;
  margin: 0;
}

@media (max-width: 768px) {
  .pcap-generator {
    padding: 1rem;
  }

  .generator-container {
    padding: 1rem;
  }

  .form-row {
    grid-template-columns: 1fr;
  }

  .action-section {
    flex-direction: column;
  }

  .action-buttons {
    flex-direction: column;
  }
}

/* ── Import from PCAP styles ── */
.import-section {
  border: 2px dashed #667eea;
  border-radius: 10px;
  padding: 0 !important;
  overflow: hidden;
}

.import-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.85rem 1.2rem;
  background: linear-gradient(135deg, #f0f4ff, #e8eeff);
  cursor: pointer;
  font-weight: 600;
  color: #667eea;
  transition: background 0.2s;
  user-select: none;
}

.import-header:hover { background: #e0e8ff; }
.import-header em { color: #999; font-weight: 400; font-size: 0.88rem; }
.import-header .chevron { font-size: 0.75rem; opacity: 0.65; }

.import-body {
  padding: 1rem 1.2rem;
  background: white;
  border-top: 1px solid #e0e8ff;
}

.import-file-row {
  display: flex;
  gap: 0.6rem;
  align-items: center;
  flex-wrap: wrap;
}

.import-select { flex: 1; min-width: 220px; }

.btn-import {
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: white;
  border: none;
  padding: 0.6rem 1.1rem;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  white-space: nowrap;
  transition: all 0.2s;
}

.btn-import:hover:not(:disabled) { transform: translateY(-1px); box-shadow: 0 4px 12px rgba(102,126,234,0.4); }
.btn-import:disabled { opacity: 0.5; cursor: not-allowed; }

.btn-refresh-files {
  background: #f4f6f8;
  border: 1px solid #ddd;
  border-radius: 8px;
  padding: 0.55rem 0.75rem;
  cursor: pointer;
  font-size: 1rem;
  transition: background 0.2s;
}

.btn-refresh-files:hover { background: #e8eeff; }

.import-error {
  color: #e74c3c;
  font-size: 0.88rem;
  margin-top: 0.6rem;
}

.import-summary {
  background: #e9f8ef;
  border: 1px solid #2ecc71;
  border-radius: 8px;
  padding: 0.55rem 0.9rem;
  margin-top: 0.75rem;
  font-size: 0.88rem;
  color: #27ae60;
}

/* ── Per-field picker ── */
.field-with-picker {
  display: flex;
  gap: 0.4rem;
  align-items: center;
}

.field-with-picker .form-control { flex: 1; }

.picker-select {
  flex-shrink: 0;
  padding: 0.45rem 0.5rem;
  border: 2px solid #667eea;
  border-radius: 8px;
  font-size: 0.8rem;
  color: #667eea;
  background: #f0f4ff;
  cursor: pointer;
  outline: none;
  min-width: 80px;
  max-width: 160px;
  transition: background 0.2s;
}

.picker-select:hover { background: #e0e8ff; }
.picker-select option { background: white; color: #333; }
</style>

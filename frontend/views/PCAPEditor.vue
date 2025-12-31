<template>
  <div class="pcap-editor-container">
    <h1>PCAP Editor</h1>

    <div class="editor-layout">
      <!-- File Upload Section -->
      <section class="upload-section">
        <div class="upload-box" @dragover.prevent @drop.prevent="handleFileDrop">
          <input
            type="file"
            ref="fileInput"
            @change="handleFileUpload"
            accept=".pcap,.pcapng"
            style="display: none"
          />
          <div @click="$refs.fileInput.click()" class="upload-content">
            <div class="upload-icon">📤</div>
            <h3>Upload PCAP File</h3>
            <p>Drag and drop or click to browse</p>
            <p class="file-formats">Supported: .pcap, .pcapng</p>
          </div>
        </div>

        <div v-if="uploadProgress" class="progress-section">
          <div class="progress-bar">
            <div class="progress-fill" :style="{ width: uploadProgress + '%' }"></div>
          </div>
          <p>{{ uploadProgress }}% uploaded</p>
        </div>

        <div v-if="fileInfo && !loading" class="file-info">
          <h3>📁 {{ fileInfo.filename }}</h3>
          <p>Total Packets: <strong>{{ fileInfo.packet_count }}</strong></p>
          <p v-if="!isModified">File Path: {{ fileInfo.filepath }}</p>
          <div v-else class="modified-info">
            <p><strong>⚠️ Working on Modified Copy</strong></p>
            <p>Original: {{ originalFilepath }}</p>
            <p>Modified: {{ fileInfo.filepath }}</p>
          </div>
        </div>
      </section>

      <!-- Packets View Section -->
      <section v-if="fileInfo" class="packets-section">
        <div class="section-header">
          <h2>Packets</h2>
          <button @click="downloadPCAP" class="btn btn-download" v-if="fileInfo">
            📥 Download {{ isModified ? 'Modified' : '' }} PCAP
          </button>
        </div>

        <div v-if="loading" class="loading">
          <p>Loading packets...</p>
        </div>

        <div v-else-if="packets.length > 0" class="packets-list">
          <div
            v-for="(packet, index) in packets"
            :key="index"
            class="packet-item"
            @click="selectPacket(index)"
            :class="{ active: selectedPacketIndex === index }"
          >
            <div class="packet-header">
              <span class="packet-index">#{{ packet.index }}</span>
              <span class="packet-length">{{ packet.length }} bytes</span>
              <span v-if="packet.src_ip" class="packet-ips">
                {{ packet.src_ip }} → {{ packet.dst_ip }}
              </span>
            </div>
            <div class="packet-summary">{{ packet.layers }}</div>
          </div>
        </div>

        <div v-else class="empty-state">
          <p>No packets found</p>
        </div>
      </section>

      <!-- Packet Details Section -->
      <section v-if="selectedPacket" class="details-section">
        <div class="section-header">
          <h2>Packet Details</h2>
          <button @click="editPayload" class="btn btn-secondary">✏️ Edit Payload</button>
        </div>

        <div class="packet-details">
          <div class="detail-item">
            <label>Index:</label>
            <span>{{ selectedPacket.index }}</span>
          </div>
          <div class="detail-item">
            <label>Length:</label>
            <span>{{ selectedPacket.length }} bytes</span>
          </div>
          <div class="detail-item">
            <label>Type:</label>
            <span>{{ selectedPacket.packet_type || 'Unknown' }}</span>
          </div>
          <div class="detail-item">
            <label>Timestamp:</label>
            <span>{{ new Date(selectedPacket.timestamp * 1000).toISOString() }}</span>
          </div>

          <!-- Editable Network Fields -->
          <div v-if="packetAnalysis && packetAnalysis.editable" class="detail-item full-width editable-section">
            <h3 class="section-title">Network Information (Editable)</h3>
            
            <!-- MAC Addresses -->
            <div v-if="packetAnalysis.src_mac" class="editable-field">
              <label>Source MAC:</label>
              <div class="editable-value">
                <input 
                  v-if="editingSrcMac" 
                  v-model="newSrcMac" 
                  type="text" 
                  class="edit-input"
                  placeholder="00:11:22:33:44:55"
                  @keyup.enter="saveMacAddresses"
                  @keyup.esc="cancelMacEdit"
                />
                <span v-else class="value-display">{{ packetAnalysis.src_mac }}</span>
                <button v-if="!editingSrcMac" @click="startEditSrcMac" class="btn-icon">✏️</button>
                <div v-else class="edit-actions">
                  <button @click="saveMacAddresses" class="btn-icon-success">✓</button>
                  <button @click="cancelMacEdit" class="btn-icon-cancel">✕</button>
                </div>
              </div>
            </div>

            <div v-if="packetAnalysis.dst_mac" class="editable-field">
              <label>Destination MAC:</label>
              <div class="editable-value">
                <input 
                  v-if="editingDstMac" 
                  v-model="newDstMac" 
                  type="text" 
                  class="edit-input"
                  placeholder="00:11:22:33:44:55"
                  @keyup.enter="saveMacAddresses"
                  @keyup.esc="cancelMacEdit"
                />
                <span v-else class="value-display">{{ packetAnalysis.dst_mac }}</span>
                <button v-if="!editingDstMac" @click="startEditDstMac" class="btn-icon">✏️</button>
                <div v-else class="edit-actions">
                  <button @click="saveMacAddresses" class="btn-icon-success">✓</button>
                  <button @click="cancelMacEdit" class="btn-icon-cancel">✕</button>
                </div>
              </div>
            </div>

            <!-- VLAN -->
            <div v-if="packetAnalysis.has_vlan" class="editable-field">
              <label>VLAN ID:</label>
              <div class="editable-value">
                <input 
                  v-if="editingVlan" 
                  v-model.number="newVlanId" 
                  type="number" 
                  class="edit-input"
                  placeholder="1-4094"
                  @keyup.enter="saveVlan"
                  @keyup.esc="cancelVlanEdit"
                />
                <span v-else class="value-display">{{ packetAnalysis.vlan_id }}</span>
                <button v-if="!editingVlan" @click="startEditVlan" class="btn-icon">✏️</button>
                <div v-else class="edit-actions">
                  <button @click="saveVlan" class="btn-icon-success">✓</button>
                  <button @click="cancelVlanEdit" class="btn-icon-cancel">✕</button>
                </div>
              </div>
            </div>

            <div v-if="!packetAnalysis.has_vlan && packetAnalysis.src_mac" class="editable-field">
              <label>VLAN (Not present):</label>
              <div class="editable-value">
                <button @click="showAddVlanDialog" class="btn-add">+ Add VLAN Tag</button>
              </div>
            </div>

            <!-- IP Addresses -->
            <div v-if="packetAnalysis.src_ip" class="editable-field">
              <label>Source IP:</label>
              <div class="editable-value">
                <input 
                  v-if="editingSrcIp" 
                  v-model="newSrcIp" 
                  type="text" 
                  class="edit-input"
                  @keyup.enter="saveIpAddresses"
                  @keyup.esc="cancelIpEdit"
                />
                <span v-else class="value-display">{{ packetAnalysis.src_ip }}</span>
                <button v-if="!editingSrcIp" @click="startEditSrcIp" class="btn-icon">✏️</button>
                <div v-else class="edit-actions">
                  <button @click="saveIpAddresses" class="btn-icon-success">✓</button>
                  <button @click="cancelIpEdit" class="btn-icon-cancel">✕</button>
                </div>
              </div>
            </div>

            <div v-if="packetAnalysis.dst_ip" class="editable-field">
              <label>Destination IP:</label>
              <div class="editable-value">
                <input 
                  v-if="editingDstIp" 
                  v-model="newDstIp" 
                  type="text" 
                  class="edit-input"
                  @keyup.enter="saveIpAddresses"
                  @keyup.esc="cancelIpEdit"
                />
                <span v-else class="value-display">{{ packetAnalysis.dst_ip }}</span>
                <button v-if="!editingDstIp" @click="startEditDstIp" class="btn-icon">✏️</button>
                <div v-else class="edit-actions">
                  <button @click="saveIpAddresses" class="btn-icon-success">✓</button>
                  <button @click="cancelIpEdit" class="btn-icon-cancel">✕</button>
                </div>
              </div>
            </div>

            <!-- Ports -->
            <div v-if="packetAnalysis.src_port" class="editable-field">
              <label>Source Port:</label>
              <div class="editable-value">
                <input 
                  v-if="editingSrcPort" 
                  v-model.number="newSrcPort" 
                  type="number" 
                  class="edit-input"
                  @keyup.enter="savePorts"
                  @keyup.esc="cancelPortEdit"
                />
                <span v-else class="value-display">{{ packetAnalysis.src_port }}</span>
                <button v-if="!editingSrcPort" @click="startEditSrcPort" class="btn-icon">✏️</button>
                <div v-else class="edit-actions">
                  <button @click="savePorts" class="btn-icon-success">✓</button>
                  <button @click="cancelPortEdit" class="btn-icon-cancel">✕</button>
                </div>
              </div>
            </div>

            <div v-if="packetAnalysis.dst_port" class="editable-field">
              <label>Destination Port:</label>
              <div class="editable-value">
                <input 
                  v-if="editingDstPort" 
                  v-model.number="newDstPort" 
                  type="number" 
                  class="edit-input"
                  @keyup.enter="savePorts"
                  @keyup.esc="cancelPortEdit"
                />
                <span v-else class="value-display">{{ packetAnalysis.dst_port }}</span>
                <button v-if="!editingDstPort" @click="startEditDstPort" class="btn-icon">✏️</button>
                <div v-else class="edit-actions">
                  <button @click="savePorts" class="btn-icon-success">✓</button>
                  <button @click="cancelPortEdit" class="btn-icon-cancel">✕</button>
                </div>
              </div>
            </div>

            <!-- HTTP Host / TLS SNI -->
            <div v-if="packetAnalysis.http_host" class="editable-field">
              <label>HTTP Host:</label>
              <div class="editable-value">
                <input 
                  v-if="editingHost" 
                  v-model="newHostValue" 
                  type="text" 
                  class="edit-input"
                  @keyup.enter="saveHttpHost"
                  @keyup.esc="cancelHostEdit"
                />
                <span v-else class="value-display">{{ packetAnalysis.http_host }}</span>
                <button v-if="!editingHost" @click="startEditHost" class="btn-icon">✏️</button>
                <div v-else class="edit-actions">
                  <button @click="saveHttpHost" class="btn-icon-success">✓</button>
                  <button @click="cancelHostEdit" class="btn-icon-cancel">✕</button>
                </div>
              </div>
            </div>

            <div v-if="packetAnalysis.dns_query" class="editable-field">
              <label>DNS Query:</label>
              <div class="editable-value">
                <input 
                  v-if="editingDns" 
                  v-model="newDnsValue" 
                  type="text" 
                  class="edit-input"
                  placeholder="example.com"
                  @keyup.enter="saveDnsQuery"
                  @keyup.esc="cancelDnsEdit"
                />
                <span v-else class="value-display">{{ packetAnalysis.dns_query }}</span>
                <button v-if="!editingDns" @click="startEditDns" class="btn-icon">✏️</button>
                <div v-else class="edit-actions">
                  <button @click="saveDnsQuery" class="btn-icon-success">✓</button>
                  <button @click="cancelDnsEdit" class="btn-icon-cancel">✕</button>
                </div>
              </div>
            </div>

            <div v-if="packetAnalysis.tls_sni" class="editable-field">
              <label>TLS SNI:</label>
              <div class="editable-value">
                <input 
                  v-if="editingSni" 
                  v-model="newSniValue" 
                  type="text" 
                  class="edit-input"
                  @keyup.enter="saveTlsSni"
                  @keyup.esc="cancelSniEdit"
                />
                <span v-else class="value-display">{{ packetAnalysis.tls_sni }}</span>
                <button v-if="!editingSni" @click="startEditSni" class="btn-icon">✏️</button>
                <div v-else class="edit-actions">
                  <button @click="saveTlsSni" class="btn-icon-success">✓</button>
                  <button @click="cancelSniEdit" class="btn-icon-cancel">✕</button>
                </div>
              </div>
            </div>
          </div>

          <div v-if="selectedPacket.payload" class="detail-item full-width">
            <label>Payload (Hex):</label>
            <div class="payload-hex">{{ selectedPacket.payload }}</div>
          </div>

          <div class="detail-item full-width">
            <label>Layers:</label>
            <div class="layers-info">{{ selectedPacket.layers }}</div>
          </div>
        </div>
      </section>

      <!-- Payload Editor Modal -->
      <div v-if="showPayloadEditor" class="modal-overlay" @click.self="closePayloadEditor">
        <div class="modal">
          <div class="modal-header">
            <h3>Edit Payload - Packet #{{ selectedPacketIndex }}</h3>
            <button @click="closePayloadEditor" class="close-btn">✕</button>
          </div>
          <div class="modal-body">
            <div class="form-group">
              <label>New Payload (Hex):</label>
              <textarea v-model="newPayload" placeholder="Enter hex payload..." rows="6"></textarea>
            </div>
            <div class="form-group">
              <label>Offset (bytes, optional):</label>
              <input v-model.number="payloadOffset" type="number" placeholder="0" />
            </div>
          </div>
          <div class="modal-footer">
            <button @click="closePayloadEditor" class="btn btn-cancel">Cancel</button>
            <button @click="savePayloadModification" class="btn btn-primary">Save Changes</button>
          </div>
        </div>
      </div>

      <!-- Add VLAN Modal -->
      <div v-if="showAddVlan" class="modal-overlay" @click.self="closeAddVlanDialog">
        <div class="modal">
          <div class="modal-header">
            <h3>Add VLAN Tag - Packet #{{ selectedPacketIndex }}</h3>
            <button @click="closeAddVlanDialog" class="close-btn">✕</button>
          </div>
          <div class="modal-body">
            <div class="form-group">
              <label>VLAN ID (1-4094):</label>
              <input v-model.number="addVlanId" type="number" min="1" max="4094" placeholder="100" />
            </div>
            <div class="form-group">
              <label>Priority (0-7, optional):</label>
              <input v-model.number="addVlanPriority" type="number" min="0" max="7" placeholder="0" />
            </div>
          </div>
          <div class="modal-footer">
            <button @click="closeAddVlanDialog" class="btn btn-cancel">Cancel</button>
            <button @click="addVlanTag" class="btn btn-primary">Add VLAN</button>
          </div>
        </div>
      </div>

      <!-- Statistics Section -->
      <section v-if="fileInfo && statistics" class="statistics-section">
        <h2>File Statistics</h2>
        <div class="stats-grid">
          <div class="stat-card">
            <h4>Total Packets</h4>
            <p class="stat-value">{{ statistics.total_packets }}</p>
          </div>
          <div class="stat-card">
            <h4>Total Size</h4>
            <p class="stat-value">{{ (statistics.total_bytes / 1024).toFixed(2) }} KB</p>
          </div>
          <div v-if="statistics.protocols" class="stat-card full-row">
            <h4>Protocols</h4>
            <div class="protocol-list">
              <span v-for="(count, proto) in statistics.protocols" :key="proto">
                {{ proto }}: {{ count }}
              </span>
            </div>
          </div>
        </div>
      </section>
    </div>

    <!-- Error Message -->
    <div v-if="error" class="error-message">
      ❌ {{ error }}
    </div>
  </div>
</template>

<script>
export default {
  name: 'PCAPEditor',
  data() {
    return {
      fileInfo: null,
      originalFilepath: null,
      isModified: false,
      packets: [],
      selectedPacket: null,
      selectedPacketIndex: null,
      statistics: null,
      loading: false,
      uploadProgress: 0,
      error: null,
      showPayloadEditor: false,
      newPayload: '',
      payloadOffset: 0,
      packetAnalysis: null,
      editingHost: false,
      editingSni: false,
      editingDns: false,
      newHostValue: '',
      newSniValue: '',
      newDnsValue: '',
      editingSrcMac: false,
      editingDstMac: false,
      newSrcMac: '',
      newDstMac: '',
      editingSrcIp: false,
      editingDstIp: false,
      newSrcIp: '',
      newDstIp: '',
      editingSrcPort: false,
      editingDstPort: false,
      newSrcPort: null,
      newDstPort: null,
      editingVlan: false,
      newVlanId: null,
      showAddVlan: false,
      addVlanId: null,
      addVlanPriority: 0,
      loadingDetails: false
    }
  },
  mounted() {
    const fileParam = this.$route.query.file
    if (fileParam) {
      this.loadFileFromPath(fileParam)
    }
  },
  methods: {
    async loadFileFromPath(filepath) {
      this.loading = true
      this.error = null

      try {
        const response = await this.$axios.get(`/pcap/${encodeURIComponent(filepath)}`)

        if (response.data.success) {
          this.fileInfo = {
            filename: response.data.file.name,
            filepath: filepath,
            packet_count: response.data.packets.length
          }
          this.originalFilepath = filepath
          this.isModified = filepath.startsWith('modified_')
          this.packets = response.data.packets
          this.statistics = response.data.statistics
          this.selectedPacket = null
          this.selectedPacketIndex = null
        } else {
          this.error = response.data.message || 'Failed to load file'
        }
      } catch (err) {
        this.error = err.response?.data?.message || err.message || 'Failed to load file'
      } finally {
        this.loading = false
      }
    },

    handleFileUpload(event) {
      const file = event.target.files[0]
      if (file) {
        this.uploadFile(file)
      }
    },

    handleFileDrop(event) {
      event.preventDefault()
      const file = event.dataTransfer.files[0]
      if (file) {
        this.uploadFile(file)
      }
    },

    uploadFile(file) {
      const formData = new FormData()
      formData.append('file', file)

      this.loading = true
      this.error = null

      this.$axios
        .post('/pcap/upload', formData, {
          headers: {
            'Content-Type': 'multipart/form-data'
          },
          onUploadProgress: (progressEvent) => {
            this.uploadProgress = Math.round(
              (progressEvent.loaded * 100) / progressEvent.total
            )
          }
        })
        .then((response) => {
          if (response.data.success) {
            this.fileInfo = response.data.data
            this.originalFilepath = response.data.data.filepath
            this.isModified = false
            this.packets = response.data.data.packets
            this.loadStatistics()
          } else {
            this.error = response.data.data.message || 'Failed to upload file'
          }
        })
        .catch((error) => {
          this.error = error.response?.data?.data?.message || 'Error uploading file'
        })
        .finally(() => {
          this.loading = false
          this.uploadProgress = 0
        })
    },

    updateToModifiedFile(modifiedFilepath) {
      // Update fileInfo to use modified file for subsequent operations
      if (!this.originalFilepath) {
        this.originalFilepath = this.fileInfo.filepath
      }
      this.fileInfo.filepath = modifiedFilepath
      this.isModified = true
    },

    selectPacket(index) {
      this.loadingDetails = true
      this.packetAnalysis = null
      this.editingHost = false
      this.editingSni = false
      
      this.$axios
        .get(`/pcap/packet/${this.fileInfo.filepath}/${index}`)
        .then((response) => {
          if (response.data.success) {
            this.selectedPacket = response.data.data
            this.selectedPacketIndex = index
            // Analyze packet for HTTP/TLS editing
            this.analyzePacket(index)
          }
        })
        .catch((error) => {
          this.error = 'Error loading packet details'
        })
        .finally(() => {
          this.loadingDetails = false
        })
    },

    analyzePacket(index) {
      this.$axios
        .get(`/pcap/analyze/${this.fileInfo.filepath}/${index}`)
        .then((response) => {
          if (response.data.success) {
            this.packetAnalysis = response.data.data
          }
        })
        .catch((error) => {
          console.error('Error analyzing packet:', error)
        })
    },

    startEditHost() {
      this.editingHost = true
      this.newHostValue = this.packetAnalysis.http_host
    },

    cancelHostEdit() {
      this.editingHost = false
      this.newHostValue = ''
    },

    saveHttpHost() {
      console.log('saveHttpHost called', this.newHostValue)
      console.log('fileInfo:', this.fileInfo)
      console.log('selectedPacketIndex:', this.selectedPacketIndex)
      console.log('$axios:', this.$axios)
      
      if (!this.newHostValue) {
        this.error = 'Host value cannot be empty'
        alert('Error: Host value cannot be empty')
        return
      }
      
      if (!this.fileInfo || this.selectedPacketIndex === null) {
        this.error = 'No packet selected'
        alert('Error: No packet selected')
        return
      }

      console.log('Making PUT request to:', `/pcap/http-host/${this.fileInfo.filepath}/${this.selectedPacketIndex}`)
      alert(`About to make request to: /pcap/http-host/${this.fileInfo.filepath}/${this.selectedPacketIndex}`)
      
      this.loading = true
      this.$axios
        .put(`/pcap/http-host/${this.fileInfo.filepath}/${this.selectedPacketIndex}`, {
          host: this.newHostValue
        })
        .then((response) => {
          console.log('Response:', response.data)
          if (response.data.success) {
            this.error = null
            // Update to modified file if returned
            if (response.data.data.modified_filepath) {
              this.updateToModifiedFile(response.data.data.modified_filepath)
            }
            alert('HTTP Host modified successfully!')
            this.editingHost = false
            // Reload packet analysis
            this.analyzePacket(this.selectedPacketIndex)
          } else {
            this.error = response.data.data?.error || response.data.error || 'Failed to modify HTTP Host'
            console.error('Failed to modify:', this.error)
          }
        })
        .catch((error) => {
          console.error('Error caught:', error)
          console.error('Error response:', error.response)
          this.error = error.response?.data?.data?.error || error.response?.data?.error || error.message || 'Error modifying HTTP Host'
        })
        .finally(() => {
          this.loading = false
        })
    },

    startEditSni() {
      this.editingSni = true
      this.newSniValue = this.packetAnalysis.tls_sni
    },

    cancelSniEdit() {
      this.editingSni = false
      this.newSniValue = ''
    },

    saveTlsSni() {
      console.log('saveTlsSni called', this.newSniValue)
      
      if (!this.newSniValue) {
        this.error = 'SNI value cannot be empty'
        return
      }

      console.log('Making PUT request to:', `/pcap/tls-sni/${this.fileInfo.filepath}/${this.selectedPacketIndex}`)
      
      this.loading = true
      this.$axios
        .put(`/pcap/tls-sni/${this.fileInfo.filepath}/${this.selectedPacketIndex}`, {
          sni: this.newSniValue
        })
        .then((response) => {
          console.log('Response:', response.data)
          if (response.data.success) {
            this.error = null
            // Update to modified file if returned
            if (response.data.data.modified_filepath) {
              this.updateToModifiedFile(response.data.data.modified_filepath)
            }
            alert('TLS SNI modified successfully!')
            this.editingSni = false
            // Reload packet analysis
            this.analyzePacket(this.selectedPacketIndex)
          } else {
            this.error = response.data.data?.error || response.data.error || 'Failed to modify TLS SNI'
            console.error('Failed to modify:', this.error)
          }
        })
        .catch((error) => {
          console.error('Error caught:', error)
          console.error('Error response:', error.response)
          this.error = error.response?.data?.data?.error || error.response?.data?.error || error.message || 'Error modifying TLS SNI'
        })
        .finally(() => {
          this.loading = false
        })
    },

    startEditDns() {
      this.editingDns = true
      this.newDnsValue = this.packetAnalysis.dns_query
    },

    cancelDnsEdit() {
      this.editingDns = false
      this.newDnsValue = ''
    },

    saveDnsQuery() {
      if (!this.newDnsValue) {
        this.error = 'DNS query cannot be empty'
        return
      }

      this.loading = true
      this.$axios
        .put(`/pcap/dns-query/${this.fileInfo.filepath}/${this.selectedPacketIndex}`, {
          query: this.newDnsValue
        })
        .then((response) => {
          if (response.data.success) {
            this.error = null
            // Update to modified file if returned
            if (response.data.data.modified_filepath) {
              this.updateToModifiedFile(response.data.data.modified_filepath)
            }
            alert('DNS query modified successfully!')
            this.editingDns = false
            // Reload packet analysis
            this.analyzePacket(this.selectedPacketIndex)
          } else {
            this.error = response.data.data?.error || response.data.error || 'Failed to modify DNS query'
          }
        })
        .catch((error) => {
          this.error = error.response?.data?.data?.error || error.response?.data?.error || error.message || 'Error modifying DNS query'
        })
        .finally(() => {
          this.loading = false
        })
    },

    editPayload() {
      this.showPayloadEditor = true
      this.newPayload = this.selectedPacket.payload || ''
      this.payloadOffset = 0
    },

    closePayloadEditor() {
      this.showPayloadEditor = false
      this.newPayload = ''
      this.payloadOffset = 0
    },

    savePayloadModification() {
      if (!this.newPayload) {
        this.error = 'Please enter a payload'
        return
      }

      this.loading = true
      this.$axios
        .put(`/pcap/packet/${this.fileInfo.filepath}/${this.selectedPacketIndex}`, {
          payload: this.newPayload,
          offset: this.payloadOffset
        })
        .then((response) => {
          if (response.data.success) {
            this.error = null
            alert('Packet modified successfully!')
            this.closePayloadEditor()
            // Reload packet details
            this.selectPacket(this.selectedPacketIndex)
          }
        })
        .catch((error) => {
          this.error = error.response?.data?.data?.message || 'Error modifying packet'
        })
        .finally(() => {
          this.loading = false
        })
    },

    downloadPCAP() {
      this.$axios
        .get(`/pcap/export/${this.fileInfo.filepath}`, {
          responseType: 'blob'
        })
        .then((response) => {
          const url = window.URL.createObjectURL(new Blob([response.data]))
          const link = document.createElement('a')
          link.href = url
          link.setAttribute('download', `modified_${this.fileInfo.filename}`)
          document.body.appendChild(link)
          link.click()
          document.body.removeChild(link)
        })
        .catch((error) => {
          this.error = 'Error downloading file'
        })
    },

    loadStatistics() {
      this.$axios
        .get(`/pcap/statistics/${this.fileInfo.filepath}`)
        .then((response) => {
          if (response.data.success) {
            this.statistics = response.data.data
          }
        })
        .catch((error) => {
          console.error('Error loading statistics:', error)
        })
    },

    // MAC Address Methods
    startEditSrcMac() {
      this.editingSrcMac = true
      this.newSrcMac = this.packetAnalysis.src_mac
    },

    startEditDstMac() {
      this.editingDstMac = true
      this.newDstMac = this.packetAnalysis.dst_mac
    },

    cancelMacEdit() {
      this.editingSrcMac = false
      this.editingDstMac = false
      this.newSrcMac = ''
      this.newDstMac = ''
    },

    saveMacAddresses() {
      this.loading = true
      const payload = {}
      if (this.editingSrcMac && this.newSrcMac) payload.src_mac = this.newSrcMac
      if (this.editingDstMac && this.newDstMac) payload.dst_mac = this.newDstMac

      this.$axios
        .put(`/pcap/mac/${this.fileInfo.filepath}/${this.selectedPacketIndex}`, payload)
        .then((response) => {
          if (response.data.success) {
            // Update to modified file if returned
            if (response.data.data.modified_filepath) {
              this.updateToModifiedFile(response.data.data.modified_filepath)
            }
            alert('MAC addresses modified successfully!')
            this.cancelMacEdit()
            this.analyzePacket(this.selectedPacketIndex)
          } else {
            this.error = response.data.error || 'Failed to modify MAC addresses'
          }
        })
        .catch((error) => {
          this.error = error.response?.data?.error || error.message || 'Error modifying MAC addresses'
        })
        .finally(() => {
          this.loading = false
        })
    },

    // IP Address Methods
    startEditSrcIp() {
      this.editingSrcIp = true
      this.newSrcIp = this.packetAnalysis.src_ip
    },

    startEditDstIp() {
      this.editingDstIp = true
      this.newDstIp = this.packetAnalysis.dst_ip
    },

    cancelIpEdit() {
      this.editingSrcIp = false
      this.editingDstIp = false
      this.newSrcIp = ''
      this.newDstIp = ''
    },

    saveIpAddresses() {
      this.loading = true
      const payload = {}
      if (this.editingSrcIp && this.newSrcIp) payload.src_ip = this.newSrcIp
      if (this.editingDstIp && this.newDstIp) payload.dst_ip = this.newDstIp

      this.$axios
        .put(`/pcap/ip/${this.fileInfo.filepath}/${this.selectedPacketIndex}`, payload)
        .then((response) => {
          if (response.data.success) {
            // Update to modified file if returned
            if (response.data.data.modified_filepath) {
              this.updateToModifiedFile(response.data.data.modified_filepath)
            }
            alert('IP addresses modified successfully!')
            this.cancelIpEdit()
            this.analyzePacket(this.selectedPacketIndex)
          } else {
            this.error = response.data.error || 'Failed to modify IP addresses'
          }
        })
        .catch((error) => {
          this.error = error.response?.data?.error || error.message || 'Error modifying IP addresses'
        })
        .finally(() => {
          this.loading = false
        })
    },

    // Port Methods
    startEditSrcPort() {
      this.editingSrcPort = true
      this.newSrcPort = this.packetAnalysis.src_port
    },

    startEditDstPort() {
      this.editingDstPort = true
      this.newDstPort = this.packetAnalysis.dst_port
    },

    cancelPortEdit() {
      this.editingSrcPort = false
      this.editingDstPort = false
      this.newSrcPort = null
      this.newDstPort = null
    },

    savePorts() {
      this.loading = true
      const payload = {}
      if (this.editingSrcPort && this.newSrcPort) payload.src_port = this.newSrcPort
      if (this.editingDstPort && this.newDstPort) payload.dst_port = this.newDstPort

      this.$axios
        .put(`/pcap/port/${this.fileInfo.filepath}/${this.selectedPacketIndex}`, payload)
        .then((response) => {
          if (response.data.success) {
            // Update to modified file if returned
            if (response.data.data.modified_filepath) {
              this.updateToModifiedFile(response.data.data.modified_filepath)
            }
            alert('Ports modified successfully!')
            this.cancelPortEdit()
            this.analyzePacket(this.selectedPacketIndex)
          } else {
            this.error = response.data.error || 'Failed to modify ports'
          }
        })
        .catch((error) => {
          this.error = error.response?.data?.error || error.message || 'Error modifying ports'
        })
        .finally(() => {
          this.loading = false
        })
    },

    // VLAN Methods
    startEditVlan() {
      this.editingVlan = true
      this.newVlanId = this.packetAnalysis.vlan_id
    },

    cancelVlanEdit() {
      this.editingVlan = false
      this.newVlanId = null
    },

    saveVlan() {
      if (!this.newVlanId || this.newVlanId < 1 || this.newVlanId > 4094) {
        this.error = 'VLAN ID must be between 1 and 4094'
        return
      }

      this.loading = true
      this.$axios
        .put(`/pcap/vlan/${this.fileInfo.filepath}/${this.selectedPacketIndex}`, {
          vlan_id: this.newVlanId
        })
        .then((response) => {
          if (response.data.success) {
            // Update to modified file if returned
            if (response.data.data.modified_filepath) {
              this.updateToModifiedFile(response.data.data.modified_filepath)
            }
            alert('VLAN modified successfully!')
            this.cancelVlanEdit()
            this.analyzePacket(this.selectedPacketIndex)
          } else {
            this.error = response.data.error || 'Failed to modify VLAN'
          }
        })
        .catch((error) => {
          this.error = error.response?.data?.error || error.message || 'Error modifying VLAN'
        })
        .finally(() => {
          this.loading = false
        })
    },

    showAddVlanDialog() {
      this.showAddVlan = true
      this.addVlanId = null
      this.addVlanPriority = 0
    },

    closeAddVlanDialog() {
      this.showAddVlan = false
      this.addVlanId = null
      this.addVlanPriority = 0
    },

    addVlanTag() {
      if (!this.addVlanId || this.addVlanId < 1 || this.addVlanId > 4094) {
        this.error = 'VLAN ID must be between 1 and 4094'
        return
      }

      this.loading = true
      this.$axios
        .post(`/pcap/vlan/${this.fileInfo.filepath}/${this.selectedPacketIndex}`, {
          vlan_id: this.addVlanId,
          priority: this.addVlanPriority
        })
        .then((response) => {
          if (response.data.success) {
            // Update to modified file if returned
            if (response.data.data.modified_filepath) {
              this.updateToModifiedFile(response.data.data.modified_filepath)
            }
            alert('VLAN tag added successfully!')
            this.closeAddVlanDialog()
            this.analyzePacket(this.selectedPacketIndex)
          } else {
            this.error = response.data.error || 'Failed to add VLAN tag'
          }
        })
        .catch((error) => {
          this.error = error.response?.data?.error || error.message || 'Error adding VLAN tag'
        })
        .finally(() => {
          this.loading = false
        })
    }
  }
}
</script>

<style scoped>
.pcap-editor-container {
  animation: fadeIn 0.5s ease-in;
  width: 100%;
  max-width: 100%;
  box-sizing: border-box;
  padding: 0 1rem;
  overflow-x: hidden;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

h1 {
  font-size: 2.5rem;
  color: #333;
  margin-bottom: 2rem;
  word-break: break-word;
  overflow-wrap: break-word;
}

.editor-layout {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 2rem;
  margin-bottom: 2rem;
  width: 100%;
  min-width: 0;
}

section {
  background: white;
  padding: 1.5rem;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  word-break: break-word;
  overflow-wrap: break-word;
  overflow: hidden;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}

.section-header h2 {
  margin: 0;
  font-size: 1.5rem;
  color: #667eea;
}

/* Upload Section */
.upload-box {
  border: 2px dashed #667eea;
  border-radius: 8px;
  padding: 2rem;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s;
  background: #f8f9ff;
}

.upload-box:hover {
  border-color: #764ba2;
  background: #ede9f6;
}

.upload-icon {
  font-size: 3rem;
  margin-bottom: 1rem;
}

.upload-content h3 {
  margin-bottom: 0.5rem;
  color: #333;
}

.file-formats {
  font-size: 0.9rem;
  color: #999;
  margin-top: 0.5rem;
}

.progress-section {
  margin-top: 1rem;
}

.progress-bar {
  height: 8px;
  background: #eee;
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: 0.5rem;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #667eea, #764ba2);
  transition: width 0.3s;
}

.file-info {
  margin-top: 1.5rem;
  padding: 1rem;
  background: #f0f4ff;
  border-radius: 8px;
  border-left: 4px solid #667eea;
}

.file-info h3 {
  color: #667eea;
  margin-bottom: 0.5rem;
}

.file-info p {
  margin: 0.3rem 0;
  color: #666;
  font-size: 0.9rem;
}

.modified-info {
  background: #fff3cd;
  padding: 0.75rem;
  border-radius: 6px;
  border-left: 4px solid #ffc107;
}

.modified-info p {
  margin: 0.3rem 0;
  color: #856404;
}

.modified-info p:first-child {
  font-weight: 700;
  color: #ff9800;
}

/* Packets Section */
.packets-list {
  max-height: 500px;
  overflow-y: auto;
}

.packet-item {
  padding: 1rem;
  border: 1px solid #eee;
  border-radius: 6px;
  margin-bottom: 0.5rem;
  cursor: pointer;
  transition: all 0.3s;
  word-break: break-word;
  overflow-wrap: break-word;
}

.packet-item:hover {
  background: #f8f9fa;
  border-color: #667eea;
}

.packet-item.active {
  background: #ede9f6;
  border-color: #667eea;
}

.packet-header {
  display: flex;
  gap: 1rem;
  margin-bottom: 0.5rem;
  flex-wrap: wrap;
  word-break: break-word;
  overflow-wrap: break-word;
}

.packet-index {
  font-weight: 600;
  color: #667eea;
  flex-shrink: 0;
}

.packet-length {
  color: #999;
  font-size: 0.9rem;
  flex-shrink: 0;
}

.packet-ips {
  color: #666;
  font-size: 0.9rem;
  word-break: break-word;
  overflow-wrap: break-word;
  flex: 1;
  min-width: 0;
}

.packet-summary {
  font-size: 0.85rem;
  color: #999;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* Details Section */
.packet-details {
  display: grid;
  gap: 1rem;
}

.detail-item {
  padding: 1rem;
  background: #f8f9fa;
  border-radius: 6px;
  display: grid;
  grid-template-columns: 150px 1fr;
  gap: 1rem;
  align-items: flex-start;
  word-break: break-word;
  overflow-wrap: break-word;
}

.detail-item.full-width {
  grid-template-columns: 1fr;
}

.detail-item label {
  font-weight: 600;
  color: #667eea;
  word-break: break-word;
}

.detail-item span {
  word-break: break-word;
  overflow-wrap: break-word;
  min-width: 0;
}

.payload-hex {
  font-family: 'Courier New', monospace;
  font-size: 0.85rem;
  word-break: break-all;
  background: white;
  padding: 0.5rem;
  border-radius: 4px;
  max-height: 150px;
  overflow-y: auto;
}

.layers-info {
  font-family: 'Courier New', monospace;
  font-size: 0.9rem;
  color: #333;
  word-break: break-all;
}

/* Modal */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal {
  background: white;
  border-radius: 12px;
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.3);
  max-width: 600px;
  width: 90%;
  max-height: 80vh;
  overflow-y: auto;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem;
  border-bottom: 1px solid #eee;
}

.modal-header h3 {
  margin: 0;
}

.close-btn {
  background: none;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
  color: #999;
}

.modal-body {
  padding: 1.5rem;
}

.form-group {
  margin-bottom: 1.5rem;
}

.form-group label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: 600;
  color: #667eea;
}

.form-group textarea,
.form-group input {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-family: 'Courier New', monospace;
  font-size: 0.9rem;
}

.form-group textarea {
  resize: vertical;
}

.modal-footer {
  display: flex;
  gap: 1rem;
  padding: 1.5rem;
  border-top: 1px solid #eee;
  justify-content: flex-end;
}

/* Statistics Section */
.statistics-section {
  grid-column: 1 / -1;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1.5rem;
}

.stat-card {
  padding: 1.5rem;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-radius: 8px;
  text-align: center;
}

.stat-card.full-row {
  grid-column: 1 / -1;
}

.stat-card h4 {
  margin: 0 0 0.5rem 0;
  opacity: 0.9;
  font-size: 0.9rem;
}

.stat-value {
  margin: 0;
  font-size: 2rem;
  font-weight: bold;
}

.protocol-list {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
  justify-content: center;
}

.protocol-list span {
  background: rgba(255, 255, 255, 0.2);
  padding: 0.5rem 1rem;
  border-radius: 4px;
}

/* Buttons */
.btn {
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 6px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
}

.btn-primary {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.btn-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.btn-secondary {
  background: #f0f4ff;
  color: #667eea;
}

.btn-secondary:hover {
  background: #ede9f6;
}

.btn-download {
  background: #28a745;
  color: white;
}

.btn-download:hover {
  background: #218838;
}

.btn-cancel {
  background: #eee;
  color: #333;
}

.btn-cancel:hover {
  background: #ddd;
}

/* Error Message */
.error-message {
  background: #fee;
  color: #c33;
  padding: 1rem;
  border-radius: 8px;
  margin-top: 1rem;
  border-left: 4px solid #c33;
}

.loading {
  text-align: center;
  padding: 2rem;
  color: #999;
}

.empty-state {
  text-align: center;
  padding: 2rem;
  color: #999;
}

/* Editable Fields Styles */
.editable-section {
  background: #f8f9ff;
  padding: 1rem;
  border-radius: 8px;
  border: 2px solid #667eea;
}

.section-title {
  font-size: 1.1rem;
  color: #667eea;
  margin-bottom: 1rem;
  padding-bottom: 0.5rem;
  border-bottom: 2px solid #667eea;
}

.editable-field {
  margin-bottom: 1rem;
}

.editable-field:last-child {
  margin-bottom: 0;
}

.editable-field label {
  font-weight: 600;
  color: #667eea;
  display: block;
  margin-bottom: 0.5rem;
}

.editable-value {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.value-display {
  flex: 1;
  padding: 0.5rem;
  background: white;
  border-radius: 4px;
  font-family: 'Courier New', monospace;
  word-break: break-word;
  overflow-wrap: break-word;
  min-width: 0;
}

.btn-add {
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: white;
  border: none;
  padding: 0.6rem 1.2rem;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 600;
  transition: all 0.3s;
}

.btn-add:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.edit-input {
  flex: 1;
  padding: 0.5rem;
  border: 2px solid #667eea;
  border-radius: 4px;
  font-family: 'Courier New', monospace;
  font-size: 0.9rem;
  word-break: break-word;
  overflow-wrap: break-word;
  min-width: 0;
}

.edit-input:focus {
  outline: none;
  border-color: #764ba2;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.btn-icon {
  background: #667eea;
  color: white;
  border: none;
  padding: 0.5rem 0.75rem;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.3s;
}

.btn-icon:hover {
  background: #764ba2;
  transform: translateY(-1px);
}

.edit-actions {
  display: flex;
  gap: 0.5rem;
}

.btn-icon-success {
  background: #28a745;
  color: white;
  border: none;
  padding: 0.5rem 0.75rem;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.3s;
}

.btn-icon-success:hover {
  background: #218838;
}

.btn-icon-cancel {
  background: #dc3545;
  color: white;
  border: none;
  padding: 0.5rem 0.75rem;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.3s;
}

.btn-icon-cancel:hover {
  background: #c82333;
}

@media (max-width: 1024px) {
  .editor-layout {
    grid-template-columns: 1fr;
  }

  .statistics-section {
    grid-column: 1;
  }
  
  .detail-item {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  h1 {
    font-size: 1.5rem;
  }

  .detail-item {
    grid-template-columns: 1fr;
    padding: 0.75rem;
  }

  .section-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 1rem;
  }
  
  section {
    padding: 1rem;
  }
  
  .editor-layout {
    gap: 1rem;
  }

  .btn {
    width: 100%;
  }
  
  .pcap-editor-container {
    padding: 0.5rem;
  }
}

@media (max-width: 480px) {
  h1 {
    font-size: 1.2rem;
  }
  
  .section-header {
    flex-direction: column;
  }
  
  .section-header h2 {
    font-size: 1.2rem;
  }
  
  .detail-item {
    grid-template-columns: 1fr;
    gap: 0.5rem;
  }
  
  .detail-item label {
    font-size: 0.9rem;
  }
  
  .packet-item {
    padding: 0.75rem;
  }
  
  .packet-header {
    flex-direction: column;
    gap: 0.25rem;
  }
}
</style>

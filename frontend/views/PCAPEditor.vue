<template>
  <div class="editor-page" @dragover.prevent @drop.prevent="handleFileDrop">
    <!-- Hidden file input -->
    <input type="file" ref="fileInput" @change="handleFileUpload" accept=".pcap,.pcapng" style="display: none" />

    <ViewHeader
      :icon="'IconEditor'"
      title="PCAP Editor"
      subtitle="Inspect, filter, and rewrite packets with automatic checksum recalculation."
    >
      <template #actions>
        <button class="btn btn-ghost" @click="$refs.fileInput.click()">
          <IconUpload :size="13"/> Upload
        </button>
        <button class="btn btn-primary" @click="downloadPCAP" :disabled="!fileInfo">
          <IconDownload :size="13"/>
          {{ isModified ? 'Download Modified PCAP' : 'Download PCAP' }}
        </button>
      </template>
    </ViewHeader>

    <!-- File Bar -->
    <div class="file-bar">
      <div v-if="fileInfo" style="display: flex; align-items: center; gap: 10px">
        <IconFiles :size="14" style="color: var(--accent-3)"/>
        <span class="mono" style="font-size: 12px">{{ fileInfo.filename }}</span>
        <Tag>pcap</Tag>
        <Tag fg="var(--text-dim)">{{ packets.length }} packets</Tag>
        <Tag v-if="statistics" fg="var(--text-dim)">{{ (statistics.total_bytes / 1024).toFixed(1) }} KB</Tag>
        <Tag v-if="isModified" fg="var(--accent-3)" bg="color-mix(in oklab, var(--accent-3) 15%, transparent)">● modified</Tag>
        
        <div v-if="uploadProgress" style="margin-left: 10px; font-size: 11px; color: var(--accent)">
          Uploading {{ uploadProgress }}%...
        </div>
        <div v-if="loading && !uploadProgress" style="margin-left: 10px; font-size: 11px; color: var(--accent)">
          Loading...
        </div>
      </div>
      <div v-else style="color: var(--text-mute); font-size: 13px">
        No file loaded. Drag & drop a .pcap file anywhere, or click Upload.
      </div>
      <div style="display: flex; gap: 6px">
        <button class="icon-btn" :class="{ active: bulkMode }" @click="toggleBulkMode">
          <IconFilter :size="13"/> Bulk Edit
        </button>
      </div>
    </div>

    <!-- Main Grid -->
    <div class="editor-grid" v-if="fileInfo">
      <!-- Packets List Pane -->
      <div class="list-pane">
        <!-- List Header -->
        <div class="list-head">
          <span v-if="bulkMode" style="width: 24px">
             <input type="checkbox" :checked="allSelected" @change="toggleSelectAll" />
          </span>
          <span style="width: 34px">#</span>
          <span style="width: 160px">time</span>
          <span style="width: 60px">type</span>
          <span style="flex: 1">length</span>
        </div>
        
        <!-- Packets Body -->
        <div class="list-body">
          <div v-if="packets.length === 0 && !loading" class="empty-state">
            No packets found.
          </div>
          <div
            v-for="(p, i) in packets"
            :key="i"
            @click="selectPacket(i)"
            class="list-row"
            :class="{ 
              active: selectedPacketIndex === i,
              'bulk-selected': bulkMode && selectedPackets.includes(i)
            }"
          >
            <span v-if="bulkMode" style="width: 24px">
              <input type="checkbox" :checked="selectedPackets.includes(i)" @change="togglePacketSelection(i)" @click.stop />
            </span>
            <span style="width: 34px; color: var(--text-mute)">{{ String(p.index).padStart(2,'0') }}</span>
            <span style="width: 160px; color: var(--text-dim)">{{ new Date(p.timestamp * 1000).toISOString() }}</span>
            <span style="width: 60px; font-weight: 500" :style="{ color: getProtoColor(p.packet_type) }">{{ p.packet_type || 'UNK' }}</span>
            <span style="flex: 1; color: selectedPacketIndex === i ? 'var(--text)' : 'var(--text-dim)'">
              {{ p.length }} bytes
              <span style="color: var(--text-mute); margin-left: 8px">· {{ p.layers }}</span>
            </span>
          </div>
        </div>
      </div>

      <!-- Detail / Bulk Pane -->
      <div class="detail-pane">
        
        <!-- Bulk Mode Panel -->
        <template v-if="bulkMode">
          <div class="detail-head">
            <span class="mono" style="font-size: 11px; color: var(--accent); letter-spacing: 0.1em">BULK EDIT MODE</span>
            <Tag fg="var(--accent)" bg="color-mix(in oklab, var(--accent) 15%, transparent)">{{ selectedPackets.length }} selected</Tag>
          </div>
          
          <div class="detail-body">
            <DetailGroup label="Bulk Modification" expanded highlight>
               <div style="margin-bottom: 12px; font-size: 12px; color: var(--text-dim)">
                 Fields left blank will not be modified.
               </div>
               <div class="bulk-form">
                 <div class="bulk-row">
                   <label>Src MAC</label>
                   <input v-model="bulkFields.src_mac" class="bulk-input mono" placeholder="leave blank" />
                 </div>
                 <div class="bulk-row">
                   <label>Dst MAC</label>
                   <input v-model="bulkFields.dst_mac" class="bulk-input mono" placeholder="leave blank" />
                 </div>
                 <div class="bulk-row">
                   <label>VLAN ID</label>
                   <input v-model.number="bulkFields.vlan_id" type="number" class="bulk-input mono" placeholder="leave blank" />
                 </div>
                 <div class="bulk-row">
                   <label>Src IP</label>
                   <input v-model="bulkFields.src_ip" class="bulk-input mono" placeholder="leave blank" />
                 </div>
                 <div class="bulk-row">
                   <label>Dst IP</label>
                   <input v-model="bulkFields.dst_ip" class="bulk-input mono" placeholder="leave blank" />
                 </div>
                 <div class="bulk-row">
                   <label>Src Port</label>
                   <input v-model.number="bulkFields.src_port" type="number" class="bulk-input mono" placeholder="leave blank" />
                 </div>
                 <div class="bulk-row">
                   <label>Dst Port</label>
                   <input v-model.number="bulkFields.dst_port" type="number" class="bulk-input mono" placeholder="leave blank" />
                 </div>
               </div>
               
               <div style="margin-top: 14px; margin-bottom: 14px">
                 <label style="display: flex; align-items: center; gap: 6px; font-size: 12px; cursor: pointer">
                   <input type="checkbox" v-model="incrementalMode" /> Incremental Mode (step: 
                   <input v-if="incrementalMode" type="number" v-model.number="incrementalStep" style="width: 40px; background: var(--panel-3); border: 1px solid var(--line); color: var(--text); padding: 2px" />)
                 </label>
                 <div v-if="incrementalMode" style="margin-top: 6px; font-size: 11px; color: var(--text-mute)">
                   Increment fields: 
                   <label><input type="checkbox" v-model="incrementalFields.src_ip"/> SrcIP</label>
                   <label><input type="checkbox" v-model="incrementalFields.dst_ip"/> DstIP</label>
                   <label><input type="checkbox" v-model="incrementalFields.src_port"/> SrcPort</label>
                   <label><input type="checkbox" v-model="incrementalFields.dst_port"/> DstPort</label>
                 </div>
               </div>
               
               <div style="display: flex; gap: 8px">
                 <button @click="applyBulkEdit" class="btn btn-primary" :disabled="bulkApplying || selectedPackets.length === 0">
                   {{ bulkApplying ? 'Applying...' : 'Apply to Selected' }}
                 </button>
                 <button @click="resetBulkFields" class="btn btn-ghost">Clear</button>
               </div>
               <div v-if="bulkResult" style="margin-top: 10px; font-size: 12px; color: var(--accent-3)">{{ bulkResult }}</div>
            </DetailGroup>
            
            <DetailGroup label="Replication" expanded>
               <div style="display: flex; gap: 10px; align-items: center; margin-bottom: 10px">
                 <span style="font-size: 12px">Repeat</span>
                 <input type="number" v-model.number="replicateCount" class="bulk-input mono" style="width: 60px" />
                 <span style="font-size: 12px">times</span>
               </div>
               <button @click="doReplicate" class="btn btn-primary" :disabled="replicating || selectedPackets.length === 0">
                 {{ replicating ? 'Replicating...' : 'Replicate Selected' }}
               </button>
               <div v-if="replicateResult" style="margin-top: 10px; font-size: 12px; color: var(--accent-2)">{{ replicateResult }}</div>
            </DetailGroup>

            <DetailGroup label="Extract" expanded>
               <div style="margin-bottom: 10px; font-size: 12px; color: var(--text-dim)">
                 Save the selected packet(s) as a new PCAP file. The current file is left unchanged.
               </div>
               <button @click="doExtract" class="btn btn-primary" :disabled="extracting || selectedPackets.length === 0">
                 {{ extracting ? 'Extracting...' : `Extract Selected (${selectedPackets.length})` }}
               </button>
               <div v-if="extractResult.filename" style="margin-top: 10px; font-size: 12px; color: var(--accent-2)">
                 ✅ Extracted {{ extractResult.packet_count }} packet(s) → <span class="mono">{{ extractResult.filename }}</span>
                 <div style="display: flex; gap: 8px; margin-top: 8px">
                   <button @click="downloadExtracted" class="btn btn-ghost" style="padding: 4px 8px"><IconDownload :size="12"/> Download</button>
                   <button @click="openExtractedInEditor" class="btn btn-ghost" style="padding: 4px 8px"><IconEditor :size="12"/> Open in Editor</button>
                 </div>
               </div>
               <div v-else-if="extractResult.error" style="margin-top: 10px; font-size: 12px; color: var(--accent-3)">❌ {{ extractResult.error }}</div>
            </DetailGroup>
          </div>
        </template>

        <!-- Single Packet Mode -->
        <template v-else>
          <div v-if="selectedPacket" class="detail-head">
            <span class="mono" style="font-size: 11px; color: var(--text-mute); letter-spacing: 0.1em">PACKET #{{ selectedPacket.index }}</span>
            <Tag :fg="getProtoColor(selectedPacket.packet_type)" :bg="`color-mix(in oklab, ${getProtoColor(selectedPacket.packet_type)} 15%, transparent)`">{{ selectedPacket.packet_type }}</Tag>
            
            <div style="margin-left: auto; display: flex; gap: 4px">
              <button @click="doMovePacket(selectedPacketIndex, 'up')" class="icon-btn" title="Move Up" :disabled="selectedPacketIndex === 0">↑</button>
              <button @click="doMovePacket(selectedPacketIndex, 'down')" class="icon-btn" title="Move Down" :disabled="selectedPacketIndex === packets.length - 1">↓</button>
              <button @click="doDuplicatePacket(selectedPacketIndex)" class="icon-btn" title="Duplicate">📋</button>
              <button @click="askDeletePacket(selectedPacketIndex)" class="icon-btn" style="color: var(--accent-3)" title="Delete">🗑️</button>
            </div>
          </div>
          <div v-if="deleteTargetIndex !== null" class="detail-head" style="background: color-mix(in oklab, var(--accent-3) 10%, transparent)">
             <span style="font-size: 12px; color: var(--accent-3)">Delete packet #{{ deleteTargetIndex }}?</span>
             <div style="margin-left: auto; display: flex; gap: 6px">
                <button @click="confirmDeletePacket" class="btn btn-primary" style="background: var(--accent-3); padding: 4px 8px">Yes</button>
                <button @click="deleteTargetIndex = null" class="btn btn-ghost" style="padding: 4px 8px">Cancel</button>
             </div>
          </div>
          
          <div v-if="selectedPacket" class="detail-body">
             <div v-if="loadingDetails" style="padding: 20px; font-size: 12px; color: var(--text-mute)">Loading packet analysis...</div>
             
             <template v-else-if="packetAnalysis">
               <DetailGroup label="Frame" expanded>
                 <EditableField label="timestamp" :value="new Date(selectedPacket.timestamp * 1000).toISOString()" readOnly />
                 <EditableField label="length" :value="`${selectedPacket.length} bytes`" readOnly />
                 <EditableField label="layers" :value="selectedPacket.layers" readOnly />
               </DetailGroup>

               <DetailGroup label="Ethernet II" expanded>
                 <EditableField label="src mac" :value="packetAnalysis.src_mac" :editing="editingSrcMac" v-model="newSrcMac" @edit="startEditSrcMac" @commit="saveMacAddresses" @cancel="cancelMacEdit" />
                 <EditableField label="dst mac" :value="packetAnalysis.dst_mac" :editing="editingDstMac" v-model="newDstMac" @edit="startEditDstMac" @commit="saveMacAddresses" @cancel="cancelMacEdit" />
                 
                 <EditableField v-if="packetAnalysis.has_vlan" label="vlan id" :value="packetAnalysis.vlan_id" :editing="editingVlan" v-model.number="newVlanId" @edit="startEditVlan" @commit="saveVlan" @cancel="cancelVlanEdit" color="var(--accent-5)" />
                 <div v-else-if="packetAnalysis.src_mac" style="padding: 4px 8px">
                    <button class="btn btn-ghost" style="padding: 2px 6px; font-size: 10px" @click="showAddVlanDialog">+ Add VLAN</button>
                 </div>
               </DetailGroup>

               <DetailGroup v-if="packetAnalysis.src_ip || packetAnalysis.dst_ip" label="IP Layer" expanded>
                 <EditableField label="src ip" :value="packetAnalysis.src_ip" :editing="editingSrcIp" v-model="newSrcIp" @edit="startEditSrcIp" @commit="saveIpAddresses" @cancel="cancelIpEdit" />
                 <EditableField label="dst ip" :value="packetAnalysis.dst_ip" :editing="editingDstIp" v-model="newDstIp" @edit="startEditDstIp" @commit="saveIpAddresses" @cancel="cancelIpEdit" />
               </DetailGroup>

               <DetailGroup v-if="packetAnalysis.src_port || packetAnalysis.dst_port" label="Transport" expanded>
                 <EditableField label="src port" :value="packetAnalysis.src_port" :editing="editingSrcPort" v-model.number="newSrcPort" @edit="startEditSrcPort" @commit="savePorts" @cancel="cancelPortEdit" />
                 <EditableField label="dst port" :value="packetAnalysis.dst_port" :editing="editingDstPort" v-model.number="newDstPort" @edit="startEditDstPort" @commit="savePorts" @cancel="cancelPortEdit" />
               </DetailGroup>

               <DetailGroup v-if="packetAnalysis.tls_sni" label="TLS" expanded highlight>
                 <EditableField label="SNI" :value="packetAnalysis.tls_sni" :editing="editingSni" v-model="newSniValue" @edit="startEditSni" @commit="saveTlsSni" @cancel="cancelSniEdit" color="var(--accent-4)" />
               </DetailGroup>

               <DetailGroup v-if="packetAnalysis.http_host" label="HTTP" expanded highlight>
                 <EditableField label="host" :value="packetAnalysis.http_host" :editing="editingHost" v-model="newHostValue" @edit="startEditHost" @commit="saveHttpHost" @cancel="cancelHostEdit" color="var(--accent-3)" />
               </DetailGroup>

               <DetailGroup v-if="packetAnalysis.dns_query" label="DNS" expanded highlight>
                 <EditableField label="query" :value="packetAnalysis.dns_query" :editing="editingDns" v-model="newDnsValue" @edit="startEditDns" @commit="saveDnsQuery" @cancel="cancelDnsEdit" color="var(--accent-5)" />
               </DetailGroup>
             </template>

             <div class="hex-strip" v-if="selectedPacket && selectedPacket.payload">
               <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px">
                 <div class="mono" style="font-size: 10.5px; color: var(--text-mute); letter-spacing: 0.1em">PAYLOAD HEX</div>
                 <button class="btn btn-ghost" style="padding: 2px 6px; font-size: 10px" @click="editPayload">Edit Payload</button>
               </div>
               <div class="mono" style="font-size: 11px; line-height: 1.6; color: var(--text-dim); word-break: break-all; white-space: pre-wrap;">{{ selectedPacket.payload }}</div>
             </div>
          </div>
          
          <div v-else-if="!loading" class="empty-state" style="margin-top: 100px">
            Select a packet to view details.
          </div>
        </template>
      </div>
    </div>
    
    <!-- Error Message -->
    <div v-if="error" class="error-strip">
       {{ error }}
    </div>

    <!-- Modals -->
    <!-- Payload Editor -->
    <div v-if="showPayloadEditor" class="modal-overlay" @click.self="closePayloadEditor">
      <div class="modal">
        <h3 style="margin: 0 0 16px; font-size: 16px">Edit Payload</h3>
        <label style="font-size: 12px; color: var(--text-dim); display: block; margin-bottom: 4px">Hex Payload</label>
        <textarea v-model="newPayload" class="mono bulk-input" rows="6" style="width: 100%; margin-bottom: 12px; resize: vertical"></textarea>
        <label style="font-size: 12px; color: var(--text-dim); display: block; margin-bottom: 4px">Offset (bytes)</label>
        <input type="number" v-model.number="payloadOffset" class="mono bulk-input" style="width: 100%; margin-bottom: 20px" />
        <div style="display: flex; justify-content: flex-end; gap: 8px">
          <button @click="closePayloadEditor" class="btn btn-ghost">Cancel</button>
          <button @click="savePayloadModification" class="btn btn-primary" :disabled="loading">Save</button>
        </div>
      </div>
    </div>
    
    <!-- Add VLAN Modal -->
    <div v-if="showAddVlan" class="modal-overlay" @click.self="closeAddVlanDialog">
      <div class="modal">
        <h3 style="margin: 0 0 16px; font-size: 16px">Add VLAN Tag</h3>
        <label style="font-size: 12px; color: var(--text-dim); display: block; margin-bottom: 4px">VLAN ID (1-4094)</label>
        <input type="number" v-model.number="addVlanId" class="mono bulk-input" style="width: 100%; margin-bottom: 12px" />
        <label style="font-size: 12px; color: var(--text-dim); display: block; margin-bottom: 4px">Priority (0-7)</label>
        <input type="number" v-model.number="addVlanPriority" class="mono bulk-input" style="width: 100%; margin-bottom: 20px" />
        <div style="display: flex; justify-content: flex-end; gap: 8px">
          <button @click="closeAddVlanDialog" class="btn btn-ghost">Cancel</button>
          <button @click="addVlanTag" class="btn btn-primary" :disabled="loading">Add VLAN</button>
        </div>
      </div>
    </div>
    
  </div>
</template>
<script>

import ViewHeader from '../components/ViewHeader.vue'
import Tag from '../components/Tag.vue'
import DetailGroup from '../components/DetailGroup.vue'
import EditableField from '../components/EditableField.vue'
import { IconEditor, IconUpload, IconDownload, IconFiles, IconFilter } from '../components/icons'

export default {
  components: { ViewHeader, Tag, DetailGroup, EditableField, IconEditor, IconUpload, IconDownload, IconFiles, IconFilter },
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
      loadingDetails: false,
      // Bulk edit state
      bulkMode: false,
      selectedPackets: [],
      bulkFields: { src_mac: '', dst_mac: '', src_ip: '', dst_ip: '', src_port: null, dst_port: null, vlan_id: null },
      keepUnselectedPackets: true,
      bulkApplying: false,
      bulkResult: '',
      // Incremental mode
      incrementalMode: false,
      incrementalStep: 1,
      incrementalFields: { src_ip: false, dst_ip: false, src_port: false, dst_port: false },
      // Replication
      showReplicatePanel: false,
      showBulkEditPanel: true,
      replicateCount: 3,
      replicateAutoSelect: true,
      replicating: false,
      replicateResult: '',
      // Extraction
      extracting: false,
      extractResult: { filename: '', filepath: '', packet_count: 0, error: '' },
      // Packet ops
      deleteTargetIndex: null
    }
  },
  mounted() {
    const fileParam = this.$route.query.file
    if (fileParam) {
      this.loadFileFromPath(fileParam)
    }
  },
  computed: {
    allSelected() {
      return this.packets.length > 0 && this.selectedPackets.length === this.packets.length
    }
  },
  methods: {
    getProtoColor(proto) {
      const colors = {
        'TCP': 'var(--accent)',
        'UDP': 'var(--accent-2)',
        'DNS': 'var(--accent-5)',
        'HTTP': 'var(--accent-3)',
        'TLS': 'var(--accent-4)'
      }
      return colors[proto] || 'var(--text-dim)'
    },
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
          this.error = response.data.data?.message || response.data.message || 'Failed to load file'
        }
      } catch (err) {
        this.error = err.response?.data?.data?.message || err.response?.data?.message || err.message || 'Failed to load file'
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
        .catch(() => {})
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
      if (!this.newHostValue) {
        this.error = 'Host value cannot be empty'
        return
      }

      if (!this.fileInfo || this.selectedPacketIndex === null) {
        this.error = 'No packet selected'
        return
      }

      this.loading = true
      this.$axios
        .put(`/pcap/http-host/${this.fileInfo.filepath}/${this.selectedPacketIndex}`, {
          host: this.newHostValue
        })
        .then((response) => {
          if (response.data.success) {
            this.error = null
            if (response.data.data.modified_filepath) {
              this.updateToModifiedFile(response.data.data.modified_filepath)
            }
            this.editingHost = false
            this.analyzePacket(this.selectedPacketIndex)
          } else {
            this.error = response.data.data?.error || response.data.error || 'Failed to modify HTTP Host'
          }
        })
        .catch((error) => {
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

      if (!this.newSniValue) {
        this.error = 'SNI value cannot be empty'
        return
      }

      this.loading = true
      this.$axios
        .put(`/pcap/tls-sni/${this.fileInfo.filepath}/${this.selectedPacketIndex}`, {
          sni: this.newSniValue
        })
        .then((response) => {
          if (response.data.success) {
            this.error = null
            if (response.data.data.modified_filepath) {
              this.updateToModifiedFile(response.data.data.modified_filepath)
            }
            this.editingSni = false
            this.analyzePacket(this.selectedPacketIndex)
          } else {
            this.error = response.data.data?.error || response.data.error || 'Failed to modify TLS SNI'
          }
        })
        .catch((error) => {
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
            this.editingDns = false
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
            this.closePayloadEditor()
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
        .catch(() => {})
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
            this.cancelMacEdit()
            this.analyzePacket(this.selectedPacketIndex)
          } else {
            this.error = response.data.data?.error || 'Failed to modify MAC addresses'
          }
        })
        .catch((error) => {
          this.error = error.response?.data?.data?.error || error.message || 'Error modifying MAC addresses'
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
            this.cancelIpEdit()
            this.analyzePacket(this.selectedPacketIndex)
          } else {
            this.error = response.data.data?.error || 'Failed to modify IP addresses'
          }
        })
        .catch((error) => {
          this.error = error.response?.data?.data?.error || error.message || 'Error modifying IP addresses'
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
            this.cancelPortEdit()
            this.analyzePacket(this.selectedPacketIndex)
          } else {
            this.error = response.data.data?.error || 'Failed to modify ports'
          }
        })
        .catch((error) => {
          this.error = error.response?.data?.data?.error || error.message || 'Error modifying ports'
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
            this.cancelVlanEdit()
            this.analyzePacket(this.selectedPacketIndex)
          } else {
            this.error = response.data.data?.error || 'Failed to modify VLAN'
          }
        })
        .catch((error) => {
          this.error = error.response?.data?.data?.error || error.message || 'Error modifying VLAN'
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
            if (response.data.data.modified_filepath) {
              this.updateToModifiedFile(response.data.data.modified_filepath)
            }
            this.closeAddVlanDialog()
            this.analyzePacket(this.selectedPacketIndex)
          } else {
            this.error = response.data.data?.error || 'Failed to add VLAN tag'
          }
        })
        .catch((error) => {
          this.error = error.response?.data?.data?.error || error.message || 'Error adding VLAN tag'
        })
        .finally(() => {
          this.loading = false
        })
    },

    // -----------------------------------------------------------------------
    // Bulk Mode
    // -----------------------------------------------------------------------
    toggleBulkMode() {
      this.bulkMode = !this.bulkMode
      if (!this.bulkMode) {
        this.selectedPackets = []
        this.bulkResult = ''
        this.replicateResult = ''
        this.extractResult = { filename: '', filepath: '', packet_count: 0, error: '' }
        this.incrementalMode = false
      }
    },

    toggleSelectAll() {
      if (this.allSelected) {
        this.selectedPackets = []
      } else {
        this.selectedPackets = this.packets.map((_, i) => i)
      }
    },

    togglePacketSelection(index) {
      const pos = this.selectedPackets.indexOf(index)
      if (pos === -1) {
        this.selectedPackets.push(index)
      } else {
        this.selectedPackets.splice(pos, 1)
      }
    },

    resetBulkFields() {
      this.bulkFields = { src_mac: '', dst_mac: '', src_ip: '', dst_ip: '', src_port: null, dst_port: null, vlan_id: null }
      this.bulkResult = ''
      this.incrementalMode = false
      this.incrementalStep = 1
      this.incrementalFields = { src_ip: false, dst_ip: false, src_port: false, dst_port: false }
    },

    async applyBulkEdit() {
      // Strip empty/null fields
      const fields = {}
      Object.entries(this.bulkFields).forEach(([k, v]) => {
        if (v !== null && v !== '') fields[k] = v
      })
      if (Object.keys(fields).length === 0) {
        this.bulkResult = '⚠️ Please fill at least one field.'
        return
      }

      // Build incremental config
      let incremental = null
      if (this.incrementalMode) {
        const incFieldList = Object.entries(this.incrementalFields)
          .filter(([, v]) => v).map(([k]) => k)
        if (incFieldList.length > 0) {
          incremental = {
            enabled: true,
            step: this.incrementalStep || 1,
            fields: incFieldList
          }
        }
      }

      this.bulkApplying = true
      this.bulkResult = ''
      try {
        const res = await this.$axios.post(
          `/pcap/bulk/${this.fileInfo.filepath}`,
          { packet_indices: this.selectedPackets, fields, incremental, keep_unselected: this.keepUnselectedPackets }
        )
        if (res.data.success) {
          const d = res.data.data
          if (d.modified_filepath) this.updateToModifiedFile(d.modified_filepath)
          this.bulkResult = `✅ Modified ${d.modified_count} of ${d.total_selected} packet(s).`
          if (d.errors && d.errors.length) this.bulkResult += ` (${d.errors.length} skipped)`
          await this.reloadPackets()
        } else {
          this.bulkResult = '❌ ' + (res.data.data?.message || res.data.message || 'Bulk edit failed')
        }
      } catch (err) {
        this.bulkResult = '❌ ' + (err.response?.data?.data?.message || err.response?.data?.message || err.message)
      } finally {
        this.bulkApplying = false
      }
    },

    async doReplicate() {
      if (this.selectedPackets.length === 0 || this.replicateCount < 1) return
      this.replicating = true
      this.replicateResult = ''
      try {
        const res = await this.$axios.post(
          `/pcap/replicate/${this.fileInfo.filepath}`,
          { packet_indices: this.selectedPackets, count: this.replicateCount }
        )
        if (res.data.success) {
          const d = res.data.data
          if (d.modified_filepath) this.updateToModifiedFile(d.modified_filepath)
          this.replicateResult = `✅ Created ${d.copy_count} copies. File now has ${d.new_packet_count} packets.`
          await this.reloadPackets()
          // Auto-select all copies if requested
          if (this.replicateAutoSelect && d.new_indices) {
            this.selectedPackets = [...d.new_indices]
          }
        } else {
          this.replicateResult = '❌ ' + (res.data.data?.message || res.data.message || 'Replication failed')
        }
      } catch (err) {
        this.replicateResult = '❌ ' + (err.response?.data?.data?.message || err.response?.data?.message || err.message)
      } finally {
        this.replicating = false
      }
    },

    // -----------------------------------------------------------------------
    // Extraction: save selected packets to a new PCAP
    // -----------------------------------------------------------------------
    async doExtract() {
      if (this.selectedPackets.length === 0) return
      this.extracting = true
      this.extractResult = { filename: '', filepath: '', packet_count: 0, error: '' }
      try {
        const res = await this.$axios.post(
          `/pcap/extract/${this.fileInfo.filepath}`,
          { packet_indices: this.selectedPackets }
        )
        if (res.data.success) {
          const d = res.data.data
          this.extractResult = { filename: d.filename, filepath: d.filepath, packet_count: d.packet_count, error: '' }
        } else {
          this.extractResult = { filename: '', filepath: '', packet_count: 0, error: res.data.data?.message || res.data.message || 'Extraction failed' }
        }
      } catch (err) {
        this.extractResult = { filename: '', filepath: '', packet_count: 0, error: err.response?.data?.data?.message || err.response?.data?.message || err.message }
      } finally {
        this.extracting = false
      }
    },

    async downloadExtracted() {
      if (!this.extractResult.filepath) return
      try {
        const response = await this.$axios.get(
          `/pcap/export/${encodeURIComponent(this.extractResult.filepath)}`,
          { responseType: 'blob' }
        )
        const url = window.URL.createObjectURL(new Blob([response.data]))
        const link = document.createElement('a')
        link.href = url
        link.setAttribute('download', this.extractResult.filename)
        document.body.appendChild(link)
        link.click()
        link.remove()
        window.URL.revokeObjectURL(url)
      } catch (err) {
        this.error = 'Error downloading extracted file'
      }
    },

    openExtractedInEditor() {
      if (!this.extractResult.filepath) return
      const fp = this.extractResult.filepath
      this.bulkMode = false
      this.selectedPackets = []
      this.extractResult = { filename: '', filepath: '', packet_count: 0, error: '' }
      this.$router.push({ name: 'pcap-editor', query: { file: fp } }).catch(() => {})
      this.loadFileFromPath(fp)
    },

    // -----------------------------------------------------------------------
    // Packet operations: delete, duplicate, move
    // -----------------------------------------------------------------------
    askDeletePacket(index) {
      this.deleteTargetIndex = index
    },

    async confirmDeletePacket() {
      if (this.deleteTargetIndex === null) return
      const idx = this.deleteTargetIndex
      this.deleteTargetIndex = null
      try {
        const res = await this.$axios.delete(`/pcap/packet/${this.fileInfo.filepath}/${idx}`)
        if (res.data.success) {
          if (res.data.data.modified_filepath) this.updateToModifiedFile(res.data.data.modified_filepath)
          if (this.selectedPacketIndex === idx) {
            this.selectedPacket = null
            this.selectedPacketIndex = null
          }
          await this.reloadPackets()
        } else {
          this.error = res.data.data?.message || res.data.message || 'Delete failed'
        }
      } catch (err) {
        this.error = err.response?.data?.data?.message || err.response?.data?.message || err.message || 'Delete failed'
      }
    },

    async doDuplicatePacket(index) {
      try {
        const res = await this.$axios.post(`/pcap/packet/${this.fileInfo.filepath}/${index}/duplicate`)
        if (res.data.success) {
          if (res.data.data.modified_filepath) this.updateToModifiedFile(res.data.data.modified_filepath)
          await this.reloadPackets()
        } else {
          this.error = res.data.data?.message || res.data.message || 'Duplicate failed'
        }
      } catch (err) {
        this.error = err.response?.data?.data?.message || err.response?.data?.message || err.message || 'Duplicate failed'
      }
    },

    async doMovePacket(index, direction) {
      try {
        const res = await this.$axios.put(
          `/pcap/packet/${this.fileInfo.filepath}/${index}/move`,
          { direction }
        )
        if (res.data.success) {
          if (res.data.data.modified_filepath) this.updateToModifiedFile(res.data.data.modified_filepath)
          // Update selected index if it was the moved packet
          if (this.selectedPacketIndex === index) {
            this.selectedPacketIndex = res.data.data.new_index
          }
          await this.reloadPackets()
        } else {
          this.error = res.data.data?.message || res.data.message || 'Move failed'
        }
      } catch (err) {
        this.error = err.response?.data?.data?.message || err.response?.data?.message || err.message || 'Move failed'
      }
    },

    async reloadPackets() {
      try {
        const res = await this.$axios.get(`/pcap/${encodeURIComponent(this.fileInfo.filepath)}`)
        if (res.data.success) {
          this.packets = res.data.packets
          this.fileInfo.packet_count = res.data.packets.length
          this.statistics = res.data.statistics
        }
      } catch (err) {
        this.error = err.message || 'Failed to reload packets'
      }
    }
  }
}
</script>
<style scoped>
.editor-page {
  display: flex;
  flex-direction: column;
  height: 100%;
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
.icon-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 10px;
  font-size: 11.5px;
  background: var(--panel-2);
  color: var(--text-dim);
  border: 1px solid var(--line);
  border-radius: 4px;
  cursor: pointer;
}
.icon-btn.active {
  background: color-mix(in oklab, var(--accent) 12%, transparent);
  color: var(--accent);
  border-color: color-mix(in oklab, var(--accent) 30%, transparent);
}
.icon-btn:hover {
  filter: brightness(1.1);
}
.editor-grid {
  display: grid;
  grid-template-columns: 1fr 400px;
  flex: 1;
  min-height: 0;
}
.list-pane {
  display: flex;
  flex-direction: column;
  background: var(--panel);
  border-right: 1px solid var(--line);
  min-width: 0;
}
.list-head {
  display: flex;
  gap: 10px;
  padding: 10px 14px;
  background: var(--panel-2);
  border-bottom: 1px solid var(--line);
  font-family: var(--mono);
  font-size: 10.5px;
  color: var(--text-mute);
  letter-spacing: 0.1em;
}
.list-body {
  overflow: auto;
  flex: 1;
}
.list-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 7px 14px;
  font-family: var(--mono);
  font-size: 11.5px;
  border-bottom: 1px solid color-mix(in oklab, var(--line) 50%, transparent);
  border-left: 2px solid transparent;
  cursor: pointer;
}
.list-row:hover {
  background: var(--panel-2);
}
.list-row.active {
  background: color-mix(in oklab, var(--accent) 10%, transparent);
  border-left-color: var(--accent);
}
.list-row.bulk-selected {
  background: color-mix(in oklab, var(--accent-2) 10%, transparent);
}
.detail-pane {
  background: var(--panel);
  overflow: auto;
  display: flex;
  flex-direction: column;
}
.detail-head {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 14px 16px;
  border-bottom: 1px solid var(--line);
  background: var(--panel-2);
}
.detail-body {
  padding: 12px;
}
.hex-strip {
  margin: 0 12px 12px;
  padding: 10px;
  background: var(--bg);
  border: 1px solid var(--line);
  border-radius: 5px;
}
.empty-state {
  text-align: center;
  padding: 40px;
  color: var(--text-mute);
  font-size: 13px;
}
.bulk-form {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.bulk-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.bulk-row label {
  font-size: 11.5px;
  color: var(--text-mute);
  font-family: var(--mono);
}
.bulk-input {
  background: var(--panel-3);
  border: 1px solid var(--line);
  border-radius: 3px;
  color: var(--text);
  padding: 4px 6px;
  font-size: 12px;
  outline: none;
  width: 160px;
  box-sizing: border-box;
}
.bulk-input:focus {
  border-color: var(--accent);
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
.modal-overlay {
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0,0,0,0.6);
  display: grid;
  place-items: center;
  z-index: 1000;
}
.modal {
  background: var(--panel);
  border: 1px solid var(--line);
  border-radius: 8px;
  padding: 20px;
  width: 400px;
  box-shadow: 0 10px 30px rgba(0,0,0,0.5);
  box-sizing: border-box;
}
</style>
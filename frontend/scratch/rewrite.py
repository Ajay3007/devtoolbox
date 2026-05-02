import os

vue_file = r"c:\Users\Ajay.Gupt\Downloads\csp\projects\devtoolbox\frontend\views\PCAPEditor.vue"

with open(vue_file, "r", encoding="utf-8") as f:
    lines = f.readlines()

# The script block is from line 605 to 1461 (index 604 to 1461)
script_lines = lines[604:1461]
script_content = "".join(script_lines)

# Ensure script_content starts with <script> and ends with </script>
if not script_content.startswith("<script>"):
    print("Error: script start not found correctly")
    exit(1)
if not script_content.strip().endswith("</script>"):
    print("Error: script end not found correctly")
    exit(1)

new_template = """<template>
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
</template>"""

new_style = """<style scoped>
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
</style>"""

# Fix up the script content to import the new components
script_lines_list = script_content.splitlines()

# find where export default is
export_idx = -1
for i, l in enumerate(script_lines_list):
    if "export default" in l:
        export_idx = i
        break

imports = """
import ViewHeader from '../components/ViewHeader.vue'
import Tag from '../components/Tag.vue'
import DetailGroup from '../components/DetailGroup.vue'
import EditableField from '../components/EditableField.vue'
import { IconEditor, IconUpload, IconDownload, IconFiles, IconFilter } from '../components/icons'
"""

script_lines_list.insert(export_idx, imports)

# We also need to add these components to the export default { components: { ... } }
# Let's see if components: { exists.
components_idx = -1
for i, l in enumerate(script_lines_list):
    if "components:" in l:
        components_idx = i
        break

if components_idx == -1:
    # insert components right after export default {
    for i, l in enumerate(script_lines_list):
        if "export default {" in l:
            script_lines_list.insert(i+1, "  components: { ViewHeader, Tag, DetailGroup, EditableField, IconEditor, IconUpload, IconDownload, IconFiles, IconFilter },")
            break
else:
    # Append to existing components
    pass # we assume it doesn't exist since there were no local components in PCAPEditor before.

# Let's add getProtoColor method
methods_idx = -1
for i, l in enumerate(script_lines_list):
    if "methods: {" in l:
        methods_idx = i
        break

if methods_idx != -1:
    protoColorMethod = """    getProtoColor(proto) {
      const colors = {
        'TCP': 'var(--accent)',
        'UDP': 'var(--accent-2)',
        'DNS': 'var(--accent-5)',
        'HTTP': 'var(--accent-3)',
        'TLS': 'var(--accent-4)'
      }
      return colors[proto] || 'var(--text-dim)'
    },"""
    script_lines_list.insert(methods_idx + 1, protoColorMethod)

final_script = "\n".join(script_lines_list)

with open(vue_file, "w", encoding="utf-8") as f:
    f.write(new_template + "\n" + final_script + "\n" + new_style)

print("Rewrote PCAPEditor.vue successfully!")

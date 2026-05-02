import os

vue_file = r"c:\Users\Ajay.Gupt\Downloads\csp\projects\devtoolbox\frontend\views\PCAPGenerator.vue"

with open(vue_file, "r", encoding="utf-8") as f:
    lines = f.readlines()

script_lines = lines[296:503]
script_content = "".join(script_lines)

new_template = """<template>
  <div class="generator-page">
    <ViewHeader
      :icon="IconGenerator"
      title="PCAP Generator"
      subtitle="Synthesize realistic traffic with full protocol flows and correct checksums."
    />
    
    <div class="main-grid">
      <!-- LEFT: config -->
      <div class="config-col">
        
        <Panel title="1. Protocol" subtitle="Each protocol determines the packet sequence and layers.">
          <div class="proto-grid">
            <button 
              v-for="p in protos" 
              :key="p.k" 
              @click="config.protocol = p.k"
              class="proto-btn"
              :class="{ active: config.protocol === p.k }"
              :style="{ 
                borderColor: config.protocol === p.k ? `color-mix(in oklab, ${p.c} 35%, transparent)` : 'var(--line)',
                background: config.protocol === p.k ? `color-mix(in oklab, ${p.c} 10%, transparent)` : 'var(--panel-2)'
              }"
            >
              <div class="proto-btn-head">
                <span class="proto-dot" :style="{ background: p.c }"></span>
                <span class="proto-label mono" :style="{ color: p.c }">{{ p.l }}</span>
              </div>
              <span class="proto-desc">{{ p.d }}</span>
            </button>
          </div>
        </Panel>

        <Panel title="2. Count & VLAN">
          <div class="field-grid">
            <Field label="packet count" v-model.number="config.packet_count" suffix="1-1000" type="number" />
            <Field label="vlan id" v-model.number="config.vlan_id" suffix="optional" />
          </div>
        </Panel>

        <Panel title="3. Network">
          <div class="field-grid">
            <Field label="src ip" v-model="config.options.src_ip">
              <template #picker v-if="hasPicks('src_ip')">
                <select class="field-picker mono" @change="applyPick('src_ip', $event.target.value); $event.target.value=''">
                  <option value="">↩ pick</option>
                  <option v-for="v in importPanel.values.src_ip" :key="v" :value="v">{{ v }}</option>
                </select>
              </template>
            </Field>
            <Field label="dst ip" v-model="config.options.dst_ip" suffix="auto ++" suffixColor="var(--accent)">
              <template #picker v-if="hasPicks('dst_ip')">
                <select class="field-picker mono" @change="applyPick('dst_ip', $event.target.value); $event.target.value=''">
                  <option value="">↩ pick</option>
                  <option v-for="v in importPanel.values.dst_ip" :key="v" :value="v">{{ v }}</option>
                </select>
              </template>
            </Field>
            <Field label="src port" v-model.number="config.options.src_port" type="number">
              <template #picker v-if="hasPicks('src_port')">
                <select class="field-picker mono" @change="applyPick('src_port', +$event.target.value); $event.target.value=''">
                  <option value="">↩ pick</option>
                  <option v-for="v in importPanel.values.src_port" :key="v" :value="v">{{ v }}</option>
                </select>
              </template>
            </Field>
            <Field label="dst port" v-model.number="config.options.dst_port" type="number">
              <template #picker v-if="hasPicks('dst_port')">
                <select class="field-picker mono" @change="applyPick('dst_port', +$event.target.value); $event.target.value=''">
                  <option value="">↩ pick</option>
                  <option v-for="v in importPanel.values.dst_port" :key="v" :value="v">{{ v }}</option>
                </select>
              </template>
            </Field>
          </div>
          
          <div style="margin-top: 10px;" v-if="hasPicks('src_mac') || hasPicks('dst_mac')">
            <div class="field-grid">
              <Field label="src mac" v-model="config.options.src_mac">
                <template #picker v-if="hasPicks('src_mac')">
                  <select class="field-picker mono" @change="applyPick('src_mac', $event.target.value); $event.target.value=''">
                    <option value="">↩ pick</option>
                    <option v-for="v in importPanel.values.src_mac" :key="v" :value="v">{{ v }}</option>
                  </select>
                </template>
              </Field>
              <Field label="dst mac" v-model="config.options.dst_mac">
                <template #picker v-if="hasPicks('dst_mac')">
                  <select class="field-picker mono" @change="applyPick('dst_mac', $event.target.value); $event.target.value=''">
                    <option value="">↩ pick</option>
                    <option v-for="v in importPanel.values.dst_mac" :key="v" :value="v">{{ v }}</option>
                  </select>
                </template>
              </Field>
            </div>
          </div>
        </Panel>

        <Panel title="4. Protocol-specific" v-if="config.protocol === 'tls' || config.protocol === 'http' || config.protocol.startsWith('dns') || config.protocol === 'icmp' || config.protocol === 'arp'">
          <Field v-if="config.protocol === 'tls'" label="SNI (server name)" v-model="config.options.tls_sni" color="var(--accent-4)"/>
          <Field v-if="config.protocol === 'http'" label="Host header" v-model="config.options.http_host" color="var(--accent-3)"/>
          <Field v-if="config.protocol.startsWith('dns')" label="query name" v-model="config.options.dns_query" color="var(--accent-5)"/>
          <Field v-if="config.protocol === 'icmp'" label="ICMP Payload" v-model="config.options.icmp_payload" color="var(--text-dim)"/>
          <Field v-if="config.protocol === 'arp'" label="Target IP" v-model="config.options.target_ip" color="var(--text-dim)"/>
        </Panel>

        <!-- Import Panel (Optional Feature in DevToolBox) -->
        <Panel title="5. Import from PCAP (Optional)">
          <div style="display: flex; gap: 6px; margin-bottom: 6px;">
            <select v-model="importPanel.selectedFile" class="mono" style="flex:1; background: var(--panel-2); border: 1px solid var(--line); border-radius: 4px; padding: 4px 6px; font-size: 11px; color: var(--text)">
              <option value="">— select an uploaded file —</option>
              <option v-for="f in importPanel.fileList" :key="f.name" :value="f.name">
                {{ f.name }} ({{ formatBytes(f.size) }})
              </option>
            </select>
            <button @click="loadFileList" class="icon-btn">🔄</button>
            <button @click="extractFieldValues" class="icon-btn" :disabled="!importPanel.selectedFile || importPanel.loading">
               {{ importPanel.loading ? '⏳' : '🔍' }} Extract
            </button>
          </div>
          <div v-if="importPanel.values" style="font-size: 11px; color: var(--accent-3)">
            Extracted from {{ importPanel.packetCount }} packets. Use ↩ pick.
          </div>
          <div v-if="importPanel.error" style="font-size: 11px; color: #e74c3c">{{ importPanel.error }}</div>
        </Panel>

        <button @click="generatePcap" :disabled="isGenerating" class="generate-btn">
          <template v-if="isGenerating">
            <span style="animation: pulse 1s infinite">●</span> Generating...
          </template>
          <template v-else>
            <IconPlay :size="13"/> Generate PCAP
          </template>
        </button>
        <div v-if="generateError" style="color: #e74c3c; font-size: 12px; margin-top: 8px;">{{ generateError }}</div>
      </div>

      <!-- RIGHT: preview -->
      <div class="preview-col">
        <Panel title="Command preview" subtitle="The equivalent scapy payload" :padding="0">
          <pre class="cmd-preview mono"><span style="color: var(--accent)">POST</span> /pcap/generate
<span style="color: var(--text-mute)">Content-Type:</span> application/json

{
  "protocol":      <span :style="{ color: currentProtoColor }">"{{ config.protocol }}"</span>,
  "packet_count":  <span style="color: var(--accent-2)">{{ config.packet_count }}</span>,
  "vlan_id":       <span style="color: var(--accent-2)">{{ config.vlan_id }}</span>,
  "options": {
    "src_ip":        <span style="color: var(--accent-2)">"{{ config.options.src_ip }}"</span>,
    "dst_ip":        <span style="color: var(--accent-2)">"{{ config.options.dst_ip }}"</span>,
    "src_port":      <span style="color: var(--accent-2)">{{ config.options.src_port }}</span>,
    "dst_port":      <span style="color: var(--accent-2)">{{ config.options.dst_port }}</span><span v-if="config.protocol === 'tls'">,
    "tls_sni":       <span style="color: var(--accent-4)">"{{ config.options.tls_sni }}"</span></span><span v-if="config.protocol === 'http'">,
    "http_host":     <span style="color: var(--accent-3)">"{{ config.options.http_host }}"</span></span><span v-if="config.protocol.startsWith('dns')">,
    "dns_query":     <span style="color: var(--accent-5)">"{{ config.options.dns_query }}"</span></span>
  }
}</pre>
        </Panel>

        <Panel :title="generatedFile ? 'Generated' : 'Output'" :subtitle="generatedFile ? `${config.packet_count * flowLength(config.protocol)} packets ready to download` : 'Click Generate to see result'">
          <div v-if="!isGenerating && !generatedFile" class="empty-output">
            <IconGenerator :size="26" style="opacity: 0.4; margin-bottom: 10px"/>
            <div>No output yet. Configure and generate.</div>
          </div>
          
          <div v-if="isGenerating" style="padding: 20px">
            <div style="font-size: 12px; color: var(--text-dim); margin-bottom: 8px; font-family: var(--mono)">
              building {{ config.protocol.toUpperCase() }} flow... {{ generateProgress }}%
            </div>
            <div style="height: 6px; background: var(--panel-3); border-radius: 3px; overflow: hidden">
              <div :style="{ width: generateProgress + '%', height: '100%', background: 'var(--accent)', transition: 'width 0.1s' }"></div>
            </div>
          </div>
          
          <div v-if="generatedFile" class="generated-output">
            <div class="file-success-pill">
              <IconCheck :size="15" style="color: var(--accent)"/>
              <span class="mono" style="font-size: 12px">{{ generatedFile }}</span>
            </div>
            <div class="stats-text mono">
              total packets  <span style="color: var(--text)">{{ generationStats.packet_count || config.packet_count * flowLength(config.protocol) }}</span><br/>
              file size      <span style="color: var(--text)">{{ formatBytes(generationStats.file_size || config.packet_count * flowLength(config.protocol) * 84) }}</span><br/>
              dst ip range   <span style="color: var(--accent-2)">{{ config.options.dst_ip }} → {{ incrementIp(config.options.dst_ip, config.packet_count - 1) }}</span><br/>
              checksums      <span style="color: var(--accent)">✓ all valid</span>
            </div>
            <div style="display: flex; gap: 8px">
              <button @click="downloadPcap" class="btn btn-primary" style="flex: 1">
                <IconDownload :size="13"/> Download
              </button>
              <button @click="openInEditor" class="btn btn-ghost" style="flex: 1">
                <IconEditor :size="13"/> Open in Editor
              </button>
            </div>
          </div>
        </Panel>

        <Panel title="Flow structure" :subtitle="`${flowLength(config.protocol)} packets per flow × ${config.packet_count} flows`">
          <FlowDiagram :proto="config.protocol"/>
        </Panel>
      </div>
    </div>
  </div>
</template>"""

new_style = """<style scoped>
.generator-page {
  display: flex;
  flex-direction: column;
  height: 100%;
}
.main-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 18px;
  padding: 8px 28px 28px;
  flex: 1;
  min-height: 0;
  overflow: auto;
}
.config-col {
  display: flex;
  flex-direction: column;
  gap: 14px;
}
.preview-col {
  display: flex;
  flex-direction: column;
  gap: 14px;
  min-width: 0;
}
.proto-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 6px;
}
.proto-btn {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 3px;
  padding: 10px 12px;
  text-align: left;
  border-radius: 5px;
  cursor: pointer;
  transition: all 0.2s;
  border: 1px solid var(--line);
}
.proto-btn-head {
  display: flex;
  align-items: center;
  gap: 8px;
}
.proto-dot {
  width: 7px;
  height: 7px;
  border-radius: 7px;
}
.proto-label {
  font-size: 12.5px;
  font-weight: 600;
}
.proto-desc {
  font-size: 11px;
  color: var(--text-dim);
}
.field-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}
.field-picker {
  position: absolute;
  right: 0;
  top: 0;
  height: 100%;
  background: var(--panel-3);
  border: 1px solid var(--line);
  border-left: none;
  border-radius: 0 4px 4px 0;
  font-size: 11px;
  color: var(--text);
  outline: none;
}
.icon-btn {
  background: var(--panel-2);
  border: 1px solid var(--line);
  border-radius: 4px;
  color: var(--text);
  cursor: pointer;
  padding: 0 8px;
}
.generate-btn {
  padding: 12px 18px;
  font-size: 13.5px;
  font-weight: 600;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  background: var(--accent);
  color: #0b0d10;
  transition: filter 0.2s;
}
.generate-btn:hover:not(:disabled) {
  filter: brightness(1.1);
}
.generate-btn:disabled {
  background: var(--panel-3);
  color: var(--text-dim);
  cursor: wait;
}
.cmd-preview {
  margin: 0;
  padding: 14px;
  background: var(--bg);
  color: var(--text-dim);
  font-size: 12px;
  line-height: 1.7;
  overflow: auto;
}
.empty-output {
  padding: 28px;
  text-align: center;
  color: var(--text-mute);
  font-size: 12.5px;
}
.generated-output {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.file-success-pill {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  background: color-mix(in oklab, var(--accent) 8%, transparent);
  border: 1px solid color-mix(in oklab, var(--accent) 25%, transparent);
  border-radius: 5px;
}
.stats-text {
  font-size: 11.5px;
  color: var(--text-dim);
  line-height: 1.7;
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
</style>"""

script_lines_list = script_content.splitlines()

# add imports
imports = """
import ViewHeader from '../components/ViewHeader.vue'
import Panel from '../components/Panel.vue'
import Field from '../components/Field.vue'
import FlowDiagram from '../components/FlowDiagram.vue'
import { IconGenerator, IconPlay, IconDownload, IconCheck, IconEditor } from '../components/icons'
"""

export_idx = -1
for i, l in enumerate(script_lines_list):
    if "export default" in l:
        export_idx = i
        break
        
script_lines_list.insert(export_idx, imports)

# add components to export default {
for i, l in enumerate(script_lines_list):
    if "export default {" in l:
        script_lines_list.insert(i+1, "  components: { ViewHeader, Panel, Field, FlowDiagram, IconGenerator, IconPlay, IconDownload, IconCheck, IconEditor },")
        break

# Add extra properties to data if they don't exist
data_idx = -1
for i, l in enumerate(script_lines_list):
    if "data() {" in l or "data () {" in l:
        data_idx = i
        break

if data_idx != -1:
    extra_data = """      protos: [
        { k: 'tcp', l: 'TCP', d: '3-way handshake + data + FIN', c: 'var(--accent)' },
        { k: 'http', l: 'HTTP', d: 'GET/200 over TCP', c: 'var(--accent-3)' },
        { k: 'udp', l: 'UDP', d: 'Stateless datagrams', c: 'var(--accent-2)' },
        { k: 'dns_udp', l: 'DNS/UDP', d: 'A, AAAA, MX queries', c: 'var(--accent-5)' },
        { k: 'dns_tcp', l: 'DNS/TCP', d: 'Large response scenarios', c: 'var(--accent-5)' },
        { k: 'tls', l: 'TLS', d: 'Client Hello + Server Hello', c: 'var(--accent-4)' },
        { k: 'icmp', l: 'ICMP', d: 'Echo req/reply', c: 'var(--text-dim)' },
        { k: 'arp', l: 'ARP', d: 'Who-has broadcasts', c: 'var(--text-dim)' }
      ],"""
    script_lines_list.insert(data_idx + 2, extra_data)

# Add extra computed properties
computed_idx = -1
for i, l in enumerate(script_lines_list):
    if "computed: {" in l:
        computed_idx = i
        break

extra_computed = """    currentProtoColor() {
      const p = this.protos.find(x => x.k === this.config.protocol)
      return p ? p.c : 'var(--accent)'
    },"""
if computed_idx != -1:
    script_lines_list.insert(computed_idx + 1, extra_computed)
else:
    # insert computed before methods
    for i, l in enumerate(script_lines_list):
        if "methods: {" in l:
            script_lines_list.insert(i, "  computed: {\n" + extra_computed + "\n  },")
            break

# Add extra methods
methods_idx = -1
for i, l in enumerate(script_lines_list):
    if "methods: {" in l:
        methods_idx = i
        break

extra_methods = """    flowLength(p) {
      return { tcp: 6, http: 8, udp: 1, dns_udp: 2, dns_tcp: 4, tls: 8, icmp: 2, arp: 1 }[p] || 1;
    },
    incrementIp(ip, n) {
      if (!ip) return '';
      const parts = ip.split('.').map(Number);
      if (parts.length !== 4 || isNaN(parts[3])) return ip;
      parts[3] = (parts[3] + n) & 0xff;
      return parts.join('.');
    },
    openInEditor() {
      this.$router.push({ name: 'PCAPEditor' })
    },"""
if methods_idx != -1:
    script_lines_list.insert(methods_idx + 1, extra_methods)

final_script = "\n".join(script_lines_list)

with open(vue_file, "w", encoding="utf-8") as f:
    f.write(new_template + "\n" + final_script + "\n" + new_style)

print("Rewrote PCAPGenerator.vue successfully!")

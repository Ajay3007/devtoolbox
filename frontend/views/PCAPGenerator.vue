<template>
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
            <div style="display: flex; align-items: center; gap: 8px">
              <label style="display: flex; align-items: center; gap: 6px; cursor: pointer; font-size: 12px; color: var(--text-dim)">
                <input type="checkbox" v-model="config.use_vlan" style="accent-color: var(--accent)" />
                enable vlan
              </label>
              <Field v-if="config.use_vlan" label="vlan id" v-model.number="config.vlan_id" type="number" style="flex: 1" />
              <span v-else style="font-size: 11px; color: var(--text-mute); font-family: var(--mono)">disabled</span>
            </div>
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
          
          <div style="margin-top: 10px;">
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

          <template v-if="config.protocol.startsWith('dns')">
            <div class="field-grid" style="margin-bottom: 6px">
              <Field label="query name" v-model="config.options.dns_query" color="var(--accent-5)"/>
              <div style="display: flex; flex-direction: column; gap: 4px">
                <label style="font-size: 10px; color: var(--text-mute); font-family: var(--mono); text-transform: lowercase; letter-spacing: 0.06em">record type</label>
                <select
                  v-model="config.options.dns_record_type"
                  class="mono"
                  style="background: var(--panel-2); border: 1px solid var(--line); border-radius: 4px; padding: 5px 8px; font-size: 12px; color: var(--accent-5); cursor: pointer"
                  @change="onDnsRecordTypeChange"
                >
                  <option value="A">A — IPv4 address</option>
                  <option value="AAAA">AAAA — IPv6 address</option>
                  <option value="CNAME">CNAME — alias</option>
                  <option value="MX">MX — mail exchange</option>
                </select>
              </div>
            </div>
            <div
              v-if="config.options.dns_record_type === 'AAAA'"
              style="font-size: 11px; color: var(--accent-5); background: color-mix(in oklab, var(--accent-5) 8%, transparent); border-radius: 4px; padding: 6px 8px; font-family: var(--mono)"
            >
              AAAA selected — set src/dst IP to IPv6 addresses (e.g. 2001:db8::1)
            </div>
            <div
              v-if="config.options.dns_record_type === 'A' && isIPv6(config.options.src_ip)"
              style="font-size: 11px; color: #e67e22; background: color-mix(in oklab, #e67e22 8%, transparent); border-radius: 4px; padding: 6px 8px; font-family: var(--mono)"
            >
              IPv6 src detected — switch to AAAA or change src IP to IPv4
            </div>
          </template>

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

        <button @click="generatePCAP" :disabled="generating" class="generate-btn">
          <template v-if="generating">
            <span style="animation: pulse 1s infinite">●</span> Generating...
          </template>
          <template v-else>
            <IconPlay :size="13"/> Generate PCAP
          </template>
        </button>
        <div v-if="error" style="color: #e74c3c; font-size: 12px; margin-top: 8px;">{{ error }}</div>
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
    "dns_query":     <span style="color: var(--accent-5)">"{{ config.options.dns_query }}"</span>,
    "dns_record_type": <span style="color: var(--accent-5)">"{{ config.options.dns_record_type }}"</span></span>
  }
}</pre>
        </Panel>

        <Panel :title="generatedFile ? 'Generated' : 'Output'" :subtitle="generatedFile ? `${config.packet_count * flowLength(config.protocol)} packets ready to download` : 'Click Generate to see result'">
          <div v-if="!generating && !generatedFile" class="empty-output">
            <IconGenerator :size="26" style="opacity: 0.4; margin-bottom: 10px"/>
            <div>No output yet. Configure and generate.</div>
          </div>
          
          <div v-if="generating" style="padding: 20px">
            <div style="font-size: 12px; color: var(--text-dim); margin-bottom: 8px; font-family: var(--mono)">
              building {{ config.protocol.toUpperCase() }} flow...
            </div>
            <div style="height: 6px; background: var(--panel-3); border-radius: 3px; overflow: hidden">
              <div :style="{ width: '100%', height: '100%', background: 'var(--accent)', transition: 'width 0.1s' }"></div>
            </div>
          </div>
          
          <div v-if="generatedFile" class="generated-output">
            <div class="file-success-pill">
              <IconCheck :size="15" style="color: var(--accent)"/>
              <span class="mono" style="font-size: 12px">{{ generatedFile.filename || generatedFile.filepath || 'output.pcap' }}</span>
            </div>
            <div class="stats-text mono">
              total packets  <span style="color: var(--text)">{{ generatedFile.packet_count || config.packet_count * flowLength(config.protocol) }}</span><br/>
              file size      <span style="color: var(--text)">{{ formatBytes(generatedFile.size || generatedFile.file_size || config.packet_count * flowLength(config.protocol) * 84) }}</span><br/>
              dst ip range   <span style="color: var(--accent-2)">{{ config.options.dst_ip }} → {{ incrementIp(config.options.dst_ip, config.packet_count - 1) }}</span><br/>
              checksums      <span style="color: var(--accent)">✓ all valid</span>
            </div>
            <div style="display: flex; gap: 8px">
              <button @click="downloadFile" class="btn btn-primary" style="flex: 1">
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
</template>
<script>
import axios from 'axios';


import ViewHeader from '../components/ViewHeader.vue'
import Panel from '../components/Panel.vue'
import Field from '../components/Field.vue'
import FlowDiagram from '../components/FlowDiagram.vue'
import { IconGenerator, IconPlay, IconDownload, IconCheck, IconEditor } from '../components/icons'

export default {
  components: { ViewHeader, Panel, Field, FlowDiagram, IconGenerator, IconPlay, IconDownload, IconCheck, IconEditor },
  name: 'PCAPGenerator',
  data() {
    return {
      protos: [
        { k: 'tcp', l: 'TCP', d: '3-way handshake + data + FIN', c: 'var(--accent)' },
        { k: 'http', l: 'HTTP', d: 'GET/200 over TCP', c: 'var(--accent-3)' },
        { k: 'udp', l: 'UDP', d: 'Stateless datagrams', c: 'var(--accent-2)' },
        { k: 'dns_udp', l: 'DNS/UDP', d: 'A, AAAA, MX queries', c: 'var(--accent-5)' },
        { k: 'dns_tcp', l: 'DNS/TCP', d: 'Large response scenarios', c: 'var(--accent-5)' },
        { k: 'tls', l: 'TLS', d: 'Client Hello + Server Hello', c: 'var(--accent-4)' },
        { k: 'icmp', l: 'ICMP', d: 'Echo req/reply', c: 'var(--text-dim)' },
        { k: 'arp', l: 'ARP', d: 'Who-has broadcasts', c: 'var(--text-dim)' }
      ],
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
          dns_record_type: 'A',
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
    currentProtoColor() {
      const p = this.protos.find(x => x.k === this.config.protocol)
      return p ? p.c : 'var(--accent)'
    },
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
    flowLength(p) {
      return { tcp: 9, http: 10, udp: 1, dns_udp: 2, dns_tcp: 9, tls: 10, icmp: 2, arp: 2 }[p] || 1;
    },
    isIPv6(ip) {
      return ip && ip.includes(':');
    },
    onDnsRecordTypeChange() {
      const type = this.config.options.dns_record_type;
      if (type === 'AAAA') {
        // Switch IPs to IPv6 example defaults if they are still the IPv4 defaults
        if (this.config.options.src_ip === '192.168.1.100') this.config.options.src_ip = '2001:db8::1';
        if (this.config.options.dst_ip === '192.168.1.200') this.config.options.dst_ip = '2001:db8::2';
      } else if (type === 'A') {
        // Switch back to IPv4 example defaults if still on example IPv6
        if (this.config.options.src_ip === '2001:db8::1') this.config.options.src_ip = '192.168.1.100';
        if (this.config.options.dst_ip === '2001:db8::2') this.config.options.dst_ip = '192.168.1.200';
      }
    },
    incrementIp(ip, n) {
      if (!ip) return '';
      // IPv6
      if (this.isIPv6(ip)) {
        try {
          const bytes = ip.split(':').flatMap(h => h ? [parseInt(h, 16) >> 8, parseInt(h, 16) & 0xff] : [0, 0]);
          // Simple last-byte increment for display
          return ip + ` (+${n})`;
        } catch { return ip; }
      }
      const parts = ip.split('.').map(Number);
      if (parts.length !== 4 || isNaN(parts[3])) return ip;
      parts[3] = (parts[3] + n) & 0xff;
      return parts.join('.');
    },
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
          this.importPanel.error = res.data.data?.message || res.data.message || 'Extraction failed';
        }
      } catch (err) {
        this.importPanel.error = err.response?.data?.data?.message || err.response?.data?.message || err.message || 'Request failed';
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
          this.error = response.data.data?.message || response.data.message || 'Failed to generate PCAP';
        }
      } catch (err) {
        this.error = err.response?.data?.data?.message || err.response?.data?.message || err.message || 'Failed to generate PCAP';
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
          dns_record_type: 'A',
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
          link.setAttribute('download', this.generatedFile.filepath.split('/').pop());
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
</style>
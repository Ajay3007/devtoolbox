<template>
  <div class="use-cases-view">
    <SectionHeading
      kicker="— WORKFLOWS"
      title="Use Cases & Workflows"
      desc="Step-by-step guides for common data-plane engineering tasks."
    />

    <div class="workflow-list">
      <div v-for="(flow, fi) in workflows" :key="fi" class="workflow-card">
        <h3 class="workflow-name">{{ flow.name }}</h3>
        <p class="workflow-desc">{{ flow.desc }}</p>
        <div class="steps">
          <div v-for="(step, si) in flow.steps" :key="si" class="step">
            <div class="step-number mono">{{ String(si + 1).padStart(2, '0') }}</div>
            <div class="step-body">
              <div class="step-tool" :style="{ color: step.color }">{{ step.tool }}</div>
              <div class="step-action">{{ step.action }}</div>
              <p class="step-detail">{{ step.detail }}</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import SectionHeading from '../components/SectionHeading.vue'

export default {
  name: 'UseCases',
  components: { SectionHeading },
  data() {
    return {
      workflows: [
        {
          name: 'Generate → Edit → Test',
          desc: 'Create synthetic traffic, rewrite headers to match your topology, then feed into your IDS/IPS for testing.',
          steps: [
            { tool: 'PCAP Generator', action: 'Synthesize 100 TLS flows', detail: 'Pick TLS protocol, set packet count to 100, configure VLAN 2018. Click Generate — a .pcap file drops into uploads/.', color: 'var(--accent-2)' },
            { tool: 'PCAP Editor', action: 'Rewrite SNI & IPs', detail: 'Open the generated file. Use Bulk Edit to rewrite all SNI fields to your target domain. Enable Incremental Mode on src_ip to fan out across a /24.', color: 'var(--accent)' },
            { tool: 'Download', action: 'Feed into IDS', detail: 'Download the modified PCAP and replay it with tcpreplay against your Suricata/Snort instance. Verify alerts fire correctly.', color: 'var(--accent-3)' },
          ]
        },
        {
          name: 'Merge → Filter → Analyze',
          desc: 'Fuse multiple capture files, filter by protocol, and deep-dive into individual payloads.',
          steps: [
            { tool: 'PCAP Merger', action: 'Combine 3 captures', detail: 'Upload captures from different TAP points. The merger preserves packet ordering and original timestamps.', color: 'var(--accent-5)' },
            { tool: 'PCAP Editor', action: 'Filter by flow', detail: 'Open the merged file. Use the protocol filter chips to isolate DNS or TLS traffic. Select specific packets for detailed inspection.', color: 'var(--accent)' },
            { tool: 'Hex Viewer', action: 'Inspect payload bytes', detail: 'Open the file in Hex Viewer. Toggle between hex and text views. Hover bytes to see offset and ASCII. Search for specific hex patterns.', color: 'var(--accent-4)' },
          ]
        },
        {
          name: 'Forensics & Comparison',
          desc: 'Load evidence captures, build comparison traffic, and perform byte-level analysis.',
          steps: [
            { tool: 'PCAP Editor', action: 'Load evidence capture', detail: 'Upload the suspicious PCAP from your incident response toolkit. Review packet list, note anomalous patterns in flags and timing.', color: 'var(--accent)' },
            { tool: 'PCAP Generator', action: 'Build comparison baseline', detail: 'Generate clean traffic matching the same protocol profile — same handshake flow, same port ranges. This is your control group.', color: 'var(--accent-2)' },
            { tool: 'Hex Viewer', action: 'Deep-dive byte comparison', detail: 'Open both files in Hex Viewer side by side. Look for anomalous byte sequences, unexpected payload lengths, or malformed headers.', color: 'var(--accent-4)' },
          ]
        },
      ]
    }
  }
}
</script>

<style scoped>
.use-cases-view {
  max-width: 900px;
  margin: 0 auto;
  padding: 24px 28px 60px;
}
.workflow-list {
  display: flex; flex-direction: column; gap: 20px;
}
.workflow-card {
  background: var(--panel);
  border: 1px solid var(--line);
  border-radius: 8px;
  padding: 20px;
}
.workflow-name {
  font-size: 18px; font-weight: 700;
  margin: 0 0 6px;
}
.workflow-desc {
  font-size: 13px; color: var(--text-dim);
  margin: 0 0 18px; line-height: 1.5;
}
.steps {
  display: flex; flex-direction: column; gap: 14px;
}
.step {
  display: flex; gap: 14px;
  padding: 12px 14px;
  background: var(--panel-2);
  border: 1px solid var(--line);
  border-radius: 6px;
}
.step-number {
  font-size: 11px; color: var(--text-mute);
  padding-top: 2px; min-width: 22px;
}
.step-body { flex: 1; }
.step-tool {
  font-family: var(--mono); font-size: 12px; font-weight: 600;
  margin-bottom: 2px;
}
.step-action {
  font-size: 14px; font-weight: 600; margin-bottom: 4px;
}
.step-detail {
  font-size: 12.5px; color: var(--text-dim);
  line-height: 1.5; margin: 0;
}
</style>

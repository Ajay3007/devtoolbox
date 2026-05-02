<template>
  <div class="top-bar">
    <div class="crumbs mono">
      <span style="color: var(--text-mute)">devtoolbox</span>
      <span style="color: var(--text-mute)">/</span>
      <span style="color: var(--text)">{{ currentLabel }}</span>
    </div>
  </div>
</template>

<script>
const ROUTE_LABELS = {
  '/': 'overview',
  '/pcap-editor': 'pcap-editor',
  '/pcap-generator': 'pcap-generator',
  '/pcap-merger': 'pcap-merger',
  '/hex-viewer': 'hex-viewer',
  '/file-manager': 'file-manager',
  '/pdf-editor': 'pdf-editor',
  '/use-cases': 'use-cases',
}

export default {
  name: 'TopBar',
  computed: {
    currentLabel() {
      return ROUTE_LABELS[this.$route.path] || this.$route.path.replace('/', '') || 'overview'
    }
  }
}
</script>

<style scoped>
.top-bar {
  position: sticky; top: 0;
  height: 48px;
  background: color-mix(in oklab, var(--bg) 85%, transparent);
  backdrop-filter: blur(8px);
  border-bottom: 1px solid var(--line);
  display: flex; align-items: center; justify-content: space-between;
  padding: 0 24px;
  z-index: 3;
}
.crumbs {
  display: flex; gap: 6px; font-size: 12px;
}
</style>

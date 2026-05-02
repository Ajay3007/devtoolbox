<template>
  <aside class="rail">
    <!-- Brand -->
    <div class="brand">
      <div class="brand-mark">
        <svg width="22" height="22" viewBox="0 0 22 22" fill="none" aria-hidden="true">
          <path d="M3 5.5 11 2l8 3.5v11L11 20l-8-3.5z" stroke="var(--accent)" stroke-width="1.4"/>
          <path d="M11 2v18M3 5.5 19 16.5M19 5.5 3 16.5" stroke="var(--accent)" stroke-width="1" opacity="0.5"/>
        </svg>
      </div>
      <div class="brand-text">
        <span class="brand-name">DevToolBox</span>
        <span class="mono brand-version">v1.0.0 · flask+scapy+vue</span>
      </div>
    </div>

    <!-- Search -->
    <div class="search-box">
      <IconSearch :size="14" style="color: var(--text-mute)" />
      <input placeholder="Jump to tool…" class="search-input" />
      <kbd class="kbd">⌘K</kbd>
    </div>

    <!-- Navigation -->
    <nav class="nav">
      <div class="nav-group" v-for="group in groups" :key="group.label">
        <div class="mono group-label">{{ group.label }}</div>
        <div class="group-items">
          <router-link
            v-for="item in group.items"
            :key="item.id"
            :to="item.route"
            custom
            v-slot="{ isActive, navigate }"
          >
            <button
              class="nav-item"
              :class="{ active: isActive, disabled: item.badge === 'soon' }"
              :disabled="item.badge === 'soon'"
              @click="item.badge !== 'soon' && navigate()"
            >
              <component :is="item.icon" :size="15" />
              <span class="nav-label">{{ item.label }}</span>
              <span v-if="item.badge === 'core'" class="badge-core">core</span>
              <span v-if="item.badge === 'soon'" class="badge-soon">soon</span>
            </button>
          </router-link>
        </div>
      </div>
    </nav>

    <!-- Status pills -->
    <div class="status-area">
      <div class="status-row">
        <span class="status-dot" style="background: var(--accent); box-shadow: 0 0 6px var(--accent)"></span>
        <span>backend</span>
        <span class="mono" style="margin-left: auto; color: var(--text-dim)">:5000</span>
      </div>
      <div class="status-row">
        <span class="status-dot" style="background: var(--accent-2); box-shadow: 0 0 6px var(--accent-2)"></span>
        <span>frontend</span>
        <span class="mono" style="margin-left: auto; color: var(--text-dim)">:8080</span>
      </div>
      <div class="mono rail-footer">
        MIT · built for data-plane engineers
      </div>
    </div>
  </aside>
</template>

<script>
import { IconSearch } from './icons'
import { IconHome, IconEditor, IconGenerator, IconMerger, IconHex, IconFiles, IconPDF, IconLog, IconUseCases, IconReceipt } from './icons'

const NAV_ITEMS = [
  { id: 'overview',   label: 'Overview',        icon: 'IconHome',      group: 'start', route: '/' },
  { id: 'editor',     label: 'PCAP Editor',     icon: 'IconEditor',    group: 'tools', route: '/pcap-editor', badge: 'core' },
  { id: 'generator',  label: 'PCAP Generator',  icon: 'IconGenerator', group: 'tools', route: '/pcap-generator' },
  { id: 'merger',     label: 'PCAP Merger',      icon: 'IconMerger',    group: 'tools', route: '/pcap-merger' },
  { id: 'hex',        label: 'Hex Viewer',       icon: 'IconHex',       group: 'tools', route: '/hex-viewer' },
  { id: 'files',      label: 'File Manager',     icon: 'IconFiles',     group: 'tools', route: '/file-manager' },
  { id: 'pdf',        label: 'PDF Editor',       icon: 'IconPDF',       group: 'tools', route: '/pdf-editor' },
  { id: 'receipt',    label: 'Receipt Editor',   icon: 'IconReceipt',   group: 'tools', route: '/receipt-editor' },
  { id: 'log',        label: 'Log Analyzer',     icon: 'IconLog',       group: 'tools', route: '#', badge: 'soon' },
  { id: 'usecases',   label: 'Use cases',        icon: 'IconUseCases',  group: 'learn', route: '/use-cases' },
]

export default {
  name: 'LeftRail',
  components: { IconSearch, IconHome, IconEditor, IconGenerator, IconMerger, IconHex, IconFiles, IconPDF, IconLog, IconUseCases, IconReceipt },
  data() {
    return {
      groups: [
        { label: 'START', items: NAV_ITEMS.filter(n => n.group === 'start') },
        { label: 'TOOLS', items: NAV_ITEMS.filter(n => n.group === 'tools') },
        { label: 'LEARN', items: NAV_ITEMS.filter(n => n.group === 'learn') },
      ]
    }
  }
}
</script>

<style scoped>
.rail {
  position: fixed;
  top: 0; left: 0; bottom: 0;
  width: 232px;
  background: var(--panel);
  border-right: 1px solid var(--line);
  display: flex;
  flex-direction: column;
  padding: 14px 10px;
  gap: 10px;
  z-index: 5;
  overflow-y: auto;
}

.brand {
  display: flex; align-items: center; gap: 10px;
  padding: 2px 6px 10px;
  border-bottom: 1px solid var(--line);
}
.brand-mark {
  width: 30px; height: 30px; border-radius: 6px;
  background: color-mix(in oklab, var(--accent) 10%, transparent);
  display: grid; place-items: center;
  border: 1px solid color-mix(in oklab, var(--accent) 25%, transparent);
}
.brand-text {
  display: flex; flex-direction: column; line-height: 1.15;
}
.brand-name {
  font-weight: 700; letter-spacing: -0.01em;
}
.brand-version {
  font-size: 10.5px; color: var(--text-mute);
}

.search-box {
  display: flex; align-items: center; gap: 6px;
  padding: 6px 8px;
  background: var(--panel-2);
  border: 1px solid var(--line);
  border-radius: 6px;
}
.search-input {
  flex: 1; background: transparent; border: none; outline: none;
  color: var(--text); font-size: 12.5px; font-family: inherit;
}
.kbd {
  font-family: var(--mono); font-size: 10px; padding: 2px 5px;
  background: var(--panel-3); border: 1px solid var(--line);
  border-radius: 3px; color: var(--text-mute);
}

.nav { display: flex; flex-direction: column; gap: 2px; }
.nav-group { margin-bottom: 10px; }
.group-label {
  font-size: 10px; color: var(--text-mute);
  letter-spacing: 0.15em; padding: 6px 10px 4px;
}
.group-items { display: flex; flex-direction: column; gap: 1px; }

.nav-item {
  display: flex; align-items: center; gap: 9px;
  padding: 7px 10px; padding-left: 8px;
  font-size: 12.8px; font-weight: 500;
  background: transparent; border: none;
  border-left: 2px solid transparent;
  border-radius: 4px; text-align: left;
  color: var(--text-dim);
  transition: background 0.12s, color 0.12s;
  width: 100%;
  font-family: inherit;
  cursor: pointer;
}
.nav-item:hover:not(.disabled) {
  background: color-mix(in oklab, var(--accent) 6%, transparent);
}
.nav-item.active {
  background: color-mix(in oklab, var(--accent) 12%, transparent);
  color: var(--text);
  border-left-color: var(--accent);
}
.nav-item.disabled {
  color: var(--text-mute);
  cursor: not-allowed;
}
.nav-label { flex: 1; text-align: left; }

.badge-core {
  font-family: var(--mono); font-size: 9.5px; padding: 1px 5px;
  background: color-mix(in oklab, var(--accent) 15%, transparent);
  color: var(--accent);
  border: 1px solid color-mix(in oklab, var(--accent) 30%, transparent);
  border-radius: 3px; letter-spacing: 0.08em;
}
.badge-soon {
  font-family: var(--mono); font-size: 9.5px; padding: 1px 5px;
  background: var(--panel-3); color: var(--text-mute);
  border: 1px solid var(--line); border-radius: 3px; letter-spacing: 0.08em;
}

.status-area {
  margin-top: auto;
  display: flex; flex-direction: column; gap: 8px;
}
.status-row {
  display: flex; align-items: center; gap: 7px;
  padding: 6px 10px; font-size: 11.5px;
  color: var(--text-dim); font-family: var(--mono);
}
.status-dot {
  width: 7px; height: 7px; border-radius: 7px;
}
.rail-footer {
  font-size: 10.5px; color: var(--text-mute);
  padding: 8px 10px; border-top: 1px solid var(--line);
}
</style>

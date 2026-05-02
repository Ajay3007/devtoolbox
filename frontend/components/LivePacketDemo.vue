<template>
  <div class="demo-wrap">
    <div class="window-bar">
      <div style="display: flex; gap: 6px">
        <span class="demo-dot" style="background: #ff5f57"></span>
        <span class="demo-dot" style="background: #febc2e"></span>
        <span class="demo-dot" style="background: #28c840"></span>
      </div>
      <span class="mono demo-title">pcap-editor — capture_20260224.pcap · 15 packets</span>
      <div style="margin-left: auto; display: flex; gap: 6px">
        <button class="play-btn" @click="playing = !playing">
          <IconPause v-if="playing" :size="11"/>
          <IconPlay v-else :size="11"/>
          {{ playing ? 'pause' : 'play' }}
        </button>
      </div>
    </div>

    <div class="demo-grid">
      <!-- packet list -->
      <div class="list-col">
        <div class="list-head">
          <span style="width: 26px">#</span>
          <span style="width: 56px">proto</span>
          <span style="flex: 1">src → dst</span>
          <span style="width: 60px; text-align: right">len</span>
        </div>
        <div v-for="(pk, i) in demoPackets" :key="pk.i"
             class="demo-row"
             :class="{ active: i === idx }"
             :style="{
               background: i === idx ? 'color-mix(in oklab, var(--accent) 10%, transparent)' : 'transparent',
               borderLeft: i === idx ? '2px solid var(--accent)' : '2px solid transparent',
               animation: i === idx ? 'flashRow 0.6s ease-out' : 'none'
             }">
          <span style="width: 26px; color: var(--text-mute)">{{ String(pk.i).padStart(2,'0') }}</span>
          <span style="width: 56px" :style="{ color: PROTO_COLOR[pk.proto] }">{{ pk.proto }}</span>
          <span style="flex: 1" :style="{ color: i === idx ? 'var(--text)' : 'var(--text-dim)' }">
            {{ pk.src }}:{{ pk.sport || '—' }} → {{ pk.dst }}:{{ pk.dport || '—' }}
          </span>
          <span style="width: 60px; text-align: right; color: var(--text-dim)">{{ pk.len }}</span>
        </div>
      </div>

      <!-- detail panel -->
      <div class="detail-col" v-if="p">
        <div class="detail-head">
          <span class="mono detail-frame">FRAME #{{ p.i }}</span>
          <Tag :fg="PROTO_COLOR[p.proto]" :bg="`color-mix(in oklab, ${PROTO_COLOR[p.proto]} 15%, transparent)`">{{ p.proto }}</Tag>
          <Tag v-if="FLAG_STYLE[p.flag]" :fg="FLAG_STYLE[p.flag].fg" :bg="FLAG_STYLE[p.flag].bg">{{ p.flag }}</Tag>
        </div>

        <div class="tree-body">
          <TreeLine label="Ethernet II" :value="`${p.src.replace(/\\..*/,'aa:bb:cc:dd:ee')}… → …`" :depth="0"/>
          <TreeLine label="IPv4" :value="`${p.src} → ${p.dst}`" :depth="1" editable/>
          <TreeLine v-if="p.proto !== 'ICMP' && p.sport > 0" :label="p.proto === 'DNS' ? 'UDP' : 'TCP/UDP'" :value="`${p.sport} → ${p.dport}`" :depth="2" editable/>
          <TreeLine v-if="p.sni" label="TLS → SNI" :value="p.sni" :depth="3" editing/>
          <TreeLine v-if="p.proto === 'DNS'" label="DNS Query" :value="p.info" :depth="3"/>
          <TreeLine v-if="p.proto === 'HTTP'" label="HTTP" :value="p.info" :depth="3"/>
        </div>

        <div class="detail-foot">
          <span class="mono" style="font-size: 11px; color: var(--text-mute)">
            t = <span style="color: var(--accent-2)">{{ p.t.toFixed(6) }}s</span> · len <span style="color: var(--accent-2)">{{ p.len }}b</span>
          </span>
          <span class="mono" style="font-size: 11px; color: var(--accent)">✓ checksum ok</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { SAMPLE_PACKETS, PROTO_COLOR, FLAG_STYLE } from '../data/sampleData'
import { IconPlay, IconPause } from './icons'
import Tag from './Tag.vue'

const TreeLine = {
  name: 'TreeLine',
  props: ['label', 'value', 'depth', 'editable', 'editing'],
  template: `
    <div class="tree-line" :class="{ editing: editing }" :style="{ paddingLeft: (10 + depth * 14) + 'px' }">
      <span style="color: var(--text-mute); margin-right: 10px">{{ depth === 0 ? '▸' : '·'.repeat(depth) }}</span>
      <span style="width: 92px; color: var(--text-dim)" class="mono">{{ label }}</span>
      <span class="mono tree-value" :class="{ editable: editable, 'is-editing': editing }">
        {{ value }}
        <span v-if="editing" style="margin-left: 2px; animation: blinkCaret 1s infinite">▍</span>
      </span>
    </div>
  `
}

export default {
  name: 'LivePacketDemo',
  components: { IconPlay, IconPause, Tag, TreeLine },
  data() {
    return {
      idx: 0,
      playing: true,
      demoPackets: SAMPLE_PACKETS.slice(0, 8),
      PROTO_COLOR,
      FLAG_STYLE
    }
  },
  computed: {
    p() {
      return this.demoPackets[this.idx]
    }
  },
  mounted() {
    this.startInterval()
  },
  unmounted() {
    this.stopInterval()
  },
  watch: {
    playing(newVal) {
      if (newVal) this.startInterval()
      else this.stopInterval()
    }
  },
  methods: {
    startInterval() {
      if (this.intervalId) return
      this.intervalId = setInterval(() => {
        this.idx = (this.idx + 1) % this.demoPackets.length
      }, 1200)
    },
    stopInterval() {
      clearInterval(this.intervalId)
      this.intervalId = null
    }
  }
}
</script>

<style scoped>
.demo-wrap {
  background: var(--panel);
  border: 1px solid var(--line);
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 20px 60px rgba(0,0,0,0.4);
}
.window-bar {
  display: flex; align-items: center; gap: 4px;
  padding: 8px 12px;
  background: var(--panel-2);
  border-bottom: 1px solid var(--line);
}
.demo-dot { width: 11px; height: 11px; border-radius: 11px; }
.demo-title { font-size: 11px; color: var(--text-mute); margin-left: 8px; }
.play-btn {
  display: inline-flex; align-items: center; gap: 4px;
  background: var(--panel-3); color: var(--text-dim);
  border: 1px solid var(--line); border-radius: 4px;
  padding: 2px 8px; font-size: 11px; font-family: var(--mono);
}
.demo-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
}
.list-col {
  border-right: 1px solid var(--line);
  font-family: var(--mono);
  font-size: 11.5px;
}
.list-head {
  display: flex; gap: 8px;
  padding: 8px 12px;
  color: var(--text-mute);
  font-size: 10.5px; letter-spacing: 0.1em;
  border-bottom: 1px solid var(--line);
  background: var(--panel-2);
}
.demo-row {
  display: flex; gap: 8px;
  padding: 7px 10px; padding-left: 10px;
  transition: all 0.2s;
}
.detail-col { display: flex; flex-direction: column; }
.detail-head {
  display: flex; align-items: center; gap: 8px;
  padding: 10px 14px;
  background: var(--panel-2);
  border-bottom: 1px solid var(--line);
}
.detail-frame { font-size: 10.5px; color: var(--text-mute); letter-spacing: 0.1em; }
.tree-body { padding: 10px 4px; flex: 1; }
.detail-foot {
  display: flex; justify-content: space-between;
  padding: 10px 14px;
  border-top: 1px solid var(--line);
  background: var(--panel-2);
}

/* TreeLine styles global within component */
:deep(.tree-line) {
  display: flex; align-items: center;
  padding: 5px 10px;
  border-left: 2px solid transparent;
  background: transparent;
  font-size: 12px;
}
:deep(.tree-line.editing) {
  border-left-color: var(--accent);
  background: color-mix(in oklab, var(--accent) 7%, transparent);
}
:deep(.tree-value) {
  color: var(--text);
  border-radius: 3px;
  padding: 0;
  border: none;
  background: transparent;
}
:deep(.tree-value.is-editing) {
  color: var(--accent);
}
:deep(.tree-value.editable) {
  background: var(--panel-3);
  padding: 1px 6px;
  border: 1px solid var(--line);
}
</style>

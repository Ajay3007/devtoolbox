<template>
  <div class="home-view">
    <!-- HERO -->
    <section class="hero-section">
      <div class="hero-content">
        <div class="mono hero-kicker">// DEVTOOLBOX v1.0.0</div>
        <h1 class="hero-title">
          Inspect packets.<br/>
          Rewrite headers.<br/>
          <span style="color: var(--accent)">Ship.</span>
        </h1>
        <p class="hero-desc">
          A browser-based suite for data-plane engineers. Generate synthetic
          PCAPs, edit captured traffic byte-by-byte, merge sessions, and
          x-ray any binary — all from one window, no install on the client.
        </p>
        <div class="hero-actions">
          <button @click="$router.push('/pcap-editor')" class="btn-primary">
            <IconEditor :size="14"/> Open PCAP Editor
          </button>
          <button @click="$router.push('/use-cases')" class="btn-ghost">
            <IconFlow :size="14"/> See workflows
          </button>
          <a class="mono hero-link" href="#">
            git clone devtoolbox.git →
          </a>
        </div>
        <div class="hero-stats">
          <div class="stat">
            <span class="mono stat-n" style="color: var(--accent)">7</span>
            <span class="mono stat-l">tools</span>
          </div>
          <div class="stat">
            <span class="mono stat-n" style="color: var(--accent-2)">8</span>
            <span class="mono stat-l">protocols</span>
          </div>
          <div class="stat">
            <span class="mono stat-n" style="color: var(--accent-3)">∞</span>
            <span class="mono stat-l">file size</span>
          </div>
          <div class="stat">
            <span class="mono stat-n" style="color: var(--accent-5)">MIT</span>
            <span class="mono stat-l">license</span>
          </div>
        </div>
      </div>
      <LivePacketDemo/>
    </section>

    <!-- TOOL GALLERY -->
    <section>
      <SectionHeading
        kicker="— THE TOOLBELT"
        title="Seven tools, one window."
        desc="Each opens in its own workspace with consistent keyboard shortcuts. Pipe output between tools — generated captures open directly in the editor, modified captures drop into the hex viewer."
      />
      <div class="gallery-grid">
        <button v-for="t in tools" :key="t.id" @click="$router.push(t.route)" class="tool-card">
          <div class="tool-head">
            <div class="tool-icon"><component :is="t.icon" :size="16"/></div>
            <span class="tool-name">{{ t.name }}</span>
            <Tag v-if="t.tag" fg="var(--accent)" bg="color-mix(in oklab, var(--accent) 15%, transparent)">{{ t.tag }}</Tag>
            <IconChevR :size="14" style="margin-left: auto; color: var(--text-mute)"/>
          </div>
          <p class="tool-desc">{{ t.desc }}</p>
          <div class="tool-preview">
            <!-- Inlined Preview Components based on Tool -->
            <template v-if="t.id === 'editor'">
              <div class="mono" style="font-size: 10px; line-height: 1.4">
                <div style="display: flex; gap: 6px; padding: 2px 0"><span style="color: var(--text-mute)">01</span><span style="color: var(--accent); width: 34px">TCP</span><span style="color: var(--text-dim)">SYN</span></div>
                <div style="display: flex; gap: 6px; padding: 2px 0"><span style="color: var(--text-mute)">02</span><span style="color: var(--accent); width: 34px">TCP</span><span style="color: var(--text-dim)">SYN-ACK</span></div>
                <div style="display: flex; gap: 6px; padding: 2px 0"><span style="color: var(--text-mute)">03</span><span style="color: var(--accent-4); width: 34px">TLS</span><span style="color: var(--text-dim)">Client Hello</span></div>
                <div style="display: flex; gap: 6px; padding: 2px 0"><span style="color: var(--text-mute)">04</span><span style="color: var(--accent-5); width: 34px">DNS</span><span style="color: var(--text-dim)">A record</span></div>
              </div>
            </template>
            <template v-if="t.id === 'generator'">
              <div class="mono" style="font-size: 10px">
                <div style="color: var(--text-dim)">protocol <span style="color: var(--accent-2)">tls</span></div>
                <div style="color: var(--text-dim)">count    <span style="color: var(--accent-2)">100</span></div>
                <div style="color: var(--text-dim)">vlan     <span style="color: var(--accent-2)">2018</span></div>
                <div style="color: var(--accent); margin-top: 4px">▸ generating…</div>
              </div>
            </template>
            <template v-if="t.id === 'merger'">
              <div class="mono" style="font-size: 10px">
                <div style="color: var(--text-dim)">a.pcap <span style="color: var(--text-mute)">24 pkts</span></div>
                <div style="color: var(--text-dim)">b.pcap <span style="color: var(--text-mute)">41 pkts</span></div>
                <div style="color: var(--text-dim)">c.pcap <span style="color: var(--text-mute)">17 pkts</span></div>
                <div style="color: var(--accent); margin-top: 4px">→ merged 82 pkts</div>
              </div>
            </template>
            <template v-if="t.id === 'hex'">
              <div class="mono" style="font-size: 9.5px; line-height: 1.35">
                <div><span style="color: var(--text-mute)">0000</span> <span style="color: var(--accent-2)">89 50 4e 47</span> 0d 0a 1a 0a  .PNG....</div>
                <div><span style="color: var(--text-mute)">0008</span> 00 00 00 0d 49 48 44 52  ....IHDR</div>
                <div><span style="color: var(--text-mute)">0010</span> 00 00 04 00 00 00 02 40  .......@</div>
              </div>
            </template>
            <template v-if="t.id === 'files'">
              <div class="mono" style="font-size: 10px">
                <div style="color: var(--text-dim)">• capture_01.pcap</div>
                <div style="color: var(--text-dim)">• firmware.bin</div>
                <div style="color: var(--text-dim)">• config.json</div>
                <div style="color: var(--text-dim)">• audit.pdf</div>
              </div>
            </template>
            <template v-if="t.id === 'pdf'">
              <div class="mono" style="font-size: 10px; color: var(--text-dim)">
                <div>page 1 of 12</div>
                <div style="margin-top: 4px">"Quarterly <span style="background: color-mix(in oklab, var(--accent) 25%, transparent); color: var(--accent)">audit▍</span>"</div>
              </div>
            </template>
          </div>
        </button>
      </div>
    </section>

    <!-- WORKFLOW -->
    <section>
      <SectionHeading
        kicker="— PIPELINES"
        title="Chain tools like Unix pipes."
        desc="Every output opens in the next tool with one click. Three common workflows:"
      />
      <div style="display: flex; flex-direction: column; gap: 10px">
        <div v-for="f in flows" :key="f.name" class="wf-row">
          <div class="wf-name">{{ f.name }}</div>
          <div class="wf-chain">
            <template v-for="(s, i) in f.steps" :key="i">
              <div class="wf-step" :style="{ borderColor: `color-mix(in oklab, ${s.c} 35%, var(--line))` }">
                <span class="wf-pill" :style="{ background: `color-mix(in oklab, ${s.c} 15%, transparent)`, color: s.c }">{{ s.t }}</span>
                <span class="mono" style="font-size: 11px; color: var(--text-dim)">{{ s.d }}</span>
              </div>
              <span v-if="i < f.steps.length - 1" style="color: var(--text-mute); font-family: var(--mono)">│</span>
            </template>
          </div>
        </div>
      </div>
    </section>

    <!-- FEATURE GRID -->
    <section>
      <SectionHeading
        kicker="— WHY IT EXISTS"
        title="Wireshark in your browser. Scapy behind the scenes."
      />
      <div class="feat-grid">
        <div v-for="ft in features" :key="ft.title" class="feat-card">
          <div class="feat-icon"><component :is="ft.icon" :size="14"/></div>
          <div class="feat-title">{{ ft.title }}</div>
          <div class="feat-desc">{{ ft.desc }}</div>
        </div>
      </div>
    </section>

    <!-- QUICKSTART -->
    <section>
      <SectionHeading
        kicker="— QUICK START"
        title="Running in 5 minutes."
        desc="Python 3.8+ and Node 14+. Two terminals, four commands."
      />
      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 14px">
        <CodeBlock title="Terminal 1 — backend" :lines="backendLines"/>
        <CodeBlock title="Terminal 2 — frontend" :lines="frontendLines"/>
      </div>
    </section>
  </div>
</template>

<script>
import SectionHeading from '../components/SectionHeading.vue'
import Tag from '../components/Tag.vue'
import LivePacketDemo from '../components/LivePacketDemo.vue'
import CodeBlock from '../components/CodeBlock.vue'
import { IconEditor, IconGenerator, IconMerger, IconHex, IconFiles, IconPDF, IconChevR, IconFlow, IconPlay, IconCheck, IconCopy } from '../components/icons'

export default {
  name: 'Home',
  components: { SectionHeading, Tag, LivePacketDemo, CodeBlock, IconEditor, IconGenerator, IconMerger, IconHex, IconFiles, IconPDF, IconChevR, IconFlow, IconPlay, IconCheck, IconCopy },
  data() {
    return {
      tools: [
        { id:'editor', route: '/pcap-editor', icon:'IconEditor', name:'PCAP Editor', tag:'core', desc:'Inspect & rewrite captures. Edit MACs, IPs, ports, VLAN, DNS, HTTP Host, TLS SNI with auto-checksums.' },
        { id:'generator', route: '/pcap-generator', icon:'IconGenerator', name:'PCAP Generator', desc:'Synthesize traffic with full TCP handshakes, DNS queries, TLS handshakes. 8 protocols, auto-incrementing IPs.' },
        { id:'merger', route: '/pcap-merger', icon:'IconMerger', name:'PCAP Merger', desc:'Combine 2+ captures into one. Preserves order and timing. Mixed PCAP/PCAPNG supported.' },
        { id:'hex', route: '/hex-viewer', icon:'IconHex', name:'Hex Viewer', desc:'Dual-view binary inspector. Auto-detect JSON/XML/text/binary. Search hex patterns or ASCII.' },
        { id:'files', route: '/file-manager', icon:'IconFiles', name:'File Manager', desc:'Browse everything in uploads/. Rename, delete, download, or open in any tool.' },
        { id:'pdf', route: '/pdf-editor', icon:'IconPDF', name:'PDF Editor', desc:'Click text in a PDF to edit in place. Preserves font size and position.' },
      ],
      flows: [
        { name: 'Generate → Edit → Test', steps: [
          { t: 'PCAP Generator', d: 'synth 100 TLS flows', c: 'var(--accent-2)' },
          { t: 'PCAP Editor',    d: 'rewrite SNI', c: 'var(--accent)' },
          { t: 'Download',       d: 'feed into IDS', c: 'var(--accent-3)' },
        ]},
        { name: 'Merge → Analyze', steps: [
          { t: 'PCAP Merger',    d: 'fuse 3 captures', c: 'var(--accent-5)' },
          { t: 'PCAP Editor',    d: 'filter by flow', c: 'var(--accent)' },
          { t: 'Hex Viewer',     d: 'inspect payload', c: 'var(--accent-4)' },
        ]},
        { name: 'Forensics', steps: [
          { t: 'PCAP Editor',    d: 'load evidence', c: 'var(--accent)' },
          { t: 'PCAP Generator', d: 'build comparison', c: 'var(--accent-2)' },
          { t: 'Hex Viewer',     d: 'deep dive bytes', c: 'var(--accent-4)' },
        ]},
      ],
      features: [
        { title: 'Zero install on the client', desc: 'Runs entirely in the browser. Share a link to your teammate; they click and use it.', icon: 'IconPlay' },
        { title: 'Powered by Scapy', desc: 'Same library Wireshark plugin authors use. Full TCP/UDP/DNS/TLS support with correct checksums.', icon: 'IconGenerator' },
        { title: 'Built for data plane', desc: 'VLAN tags, dual-stack IPv4/v6, CIDR, protocol reverse-engineering. Not consumer-grade.', icon: 'IconEditor' },
        { title: 'API-first', desc: '/api/* endpoints exposed. Automate from CI, scripts, or other tools.', icon: 'IconHex' },
        { title: 'Auto-checksum', desc: 'Modify an IP, port, or payload — TCP/UDP/v4/v6 checksums recompute on save.', icon: 'IconCheck' },
        { title: 'Inline editing', desc: 'Click any field in the packet tree to edit. No pop-up modals, no forms.', icon: 'IconCopy' },
      ],
      backendLines: [
        { c: 'python -m venv .venv', out: null },
        { c: 'source .venv/bin/activate', out: null },
        { c: 'cd backend && pip install -r requirements.txt', out: null },
        { c: 'python app.py', out: '✓ serving at http://localhost:5000' },
      ],
      frontendLines: [
        { c: 'cd frontend', out: null },
        { c: 'npm install', out: null },
        { c: 'npm run dev', out: '✓ local: http://localhost:8080' },
        { c: 'open http://localhost:8080', out: null },
      ]
    }
  }
}
</script>

<style scoped>
.home-view {
  max-width: 1180px;
  margin: 0 auto;
  padding: 24px 28px 60px;
  display: flex; flex-direction: column; gap: 48px;
}

/* HERO */
.hero-section {
  display: grid; grid-template-columns: 1fr 1.15fr; gap: 32px; align-items: center; margin-top: 8px;
}
.hero-kicker {
  color: var(--accent); font-size: 11.5px; letter-spacing: 0.2em; margin-bottom: 14px;
}
.hero-title {
  font-size: 46px; line-height: 1.05; letter-spacing: -0.03em; margin: 0; font-weight: 700;
}
.hero-desc {
  font-size: 15.5px; color: var(--text-dim); line-height: 1.55; max-width: 480px; margin-top: 18px;
}
.hero-actions {
  display: flex; gap: 10px; margin-top: 22px; flex-wrap: wrap;
}
.btn-primary {
  display: inline-flex; align-items: center; gap: 7px;
  padding: 10px 16px; font-size: 13px; font-weight: 600;
  background: var(--accent); color: #0b0d10;
  border: none; border-radius: 6px;
}
.btn-ghost {
  display: inline-flex; align-items: center; gap: 7px;
  padding: 10px 16px; font-size: 13px; font-weight: 500;
  background: transparent; color: var(--text);
  border: 1px solid var(--line-2); border-radius: 6px;
}
.hero-link {
  font-size: 12px; color: var(--text-dim); text-decoration: none; padding: 10px 4px;
}
.hero-stats {
  display: flex; gap: 18px; margin-top: 28px; flex-wrap: wrap;
}
.stat { display: flex; flex-direction: column; }
.stat-n { font-size: 22px; letter-spacing: -0.02em; font-weight: 600; }
.stat-l { font-size: 10.5px; color: var(--text-mute); letter-spacing: 0.1em; }

/* GALLERY */
.gallery-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; }
.tool-card {
  background: var(--panel); border: 1px solid var(--line);
  border-radius: 8px; padding: 16px; text-align: left;
  display: flex; flex-direction: column; gap: 10px;
  color: var(--text); transition: border-color 0.15s, transform 0.15s;
  cursor: pointer;
  font-family: inherit;
}
.tool-card:hover { border-color: color-mix(in oklab, var(--accent) 30%, var(--line)); }
.tool-head { display: flex; align-items: center; gap: 8px; }
.tool-icon {
  width: 28px; height: 28px; border-radius: 6px;
  background: var(--panel-3); border: 1px solid var(--line);
  display: grid; place-items: center; color: var(--accent);
}
.tool-name { font-weight: 600; font-size: 14px; }
.tool-desc { font-size: 12.5px; color: var(--text-dim); line-height: 1.5; margin: 0; min-height: 56px; }
.tool-preview {
  background: var(--bg); border: 1px solid var(--line);
  border-radius: 5px; padding: 10px; min-height: 70px;
}

/* FLOWS */
.wf-row {
  display: flex; align-items: center; gap: 16px;
  padding: 14px 16px;
  background: var(--panel); border: 1px solid var(--line); border-radius: 6px;
}
.wf-name {
  font-size: 12px; color: var(--text-dim); font-family: var(--mono);
  width: 180px; letter-spacing: 0.03em;
}
.wf-chain { display: flex; align-items: center; gap: 10px; flex: 1; flex-wrap: wrap; }
.wf-step {
  display: flex; align-items: center; gap: 10px;
  padding: 6px 10px; border: 1px solid var(--line); border-radius: 5px;
  background: var(--panel-2);
}
.wf-pill {
  font-size: 11px; padding: 2px 7px; border-radius: 3px;
  font-family: var(--mono); font-weight: 500;
}

/* FEATURES */
.feat-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px; }
.feat-card {
  background: var(--panel); border: 1px solid var(--line);
  border-radius: 6px; padding: 14px;
}
.feat-icon {
  width: 26px; height: 26px; border-radius: 5px;
  background: color-mix(in oklab, var(--accent) 12%, transparent);
  color: var(--accent);
  display: grid; place-items: center; margin-bottom: 10px;
}
.feat-title { font-weight: 600; font-size: 13.5px; margin-bottom: 4px; }
.feat-desc { font-size: 12.5px; color: var(--text-dim); line-height: 1.5; }
</style>

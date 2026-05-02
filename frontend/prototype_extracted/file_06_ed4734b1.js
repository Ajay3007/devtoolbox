/* Overview / landing view — hero with live PCAP demo, tool gallery, workflow */

function LivePacketDemo() {
  const [idx, setIdx] = React.useState(0);
  const [playing, setPlaying] = React.useState(true);
  const demoPackets = SAMPLE_PACKETS.slice(0, 8);

  React.useEffect(() => {
    if (!playing) return;
    const id = setInterval(() => setIdx(v => (v + 1) % demoPackets.length), 1200);
    return () => clearInterval(id);
  }, [playing]);

  const p = demoPackets[idx];
  return (
    <div style={demoStyles.wrap}>
      <div style={demoStyles.windowBar}>
        <div style={{ display: 'flex', gap: 6 }}>
          <span style={{ ...demoStyles.dot, background: '#ff5f57' }}/>
          <span style={{ ...demoStyles.dot, background: '#febc2e' }}/>
          <span style={{ ...demoStyles.dot, background: '#28c840' }}/>
        </div>
        <span className="mono" style={{ fontSize: 11, color: 'var(--text-mute)', marginLeft: 8 }}>
          pcap-editor — capture_20260224.pcap · 15 packets
        </span>
        <div style={{ marginLeft: 'auto', display: 'flex', gap: 6 }}>
          <button onClick={() => setPlaying(p => !p)} style={demoStyles.playBtn}>
            {playing ? <IconPause size={11}/> : <IconPlay size={11}/>}
            {playing ? 'pause' : 'play'}
          </button>
        </div>
      </div>

      <div style={demoStyles.grid}>
        {/* packet list */}
        <div style={demoStyles.listCol}>
          <div style={demoStyles.listHead}>
            <span style={{ width: 26 }}>#</span>
            <span style={{ width: 56 }}>proto</span>
            <span style={{ flex: 1 }}>src → dst</span>
            <span style={{ width: 60, textAlign: 'right' }}>len</span>
          </div>
          {demoPackets.map((pk, i) => {
            const active = i === idx;
            const color = PROTO_COLOR[pk.proto];
            return (
              <div key={pk.i} style={{
                ...demoStyles.row,
                background: active ? 'color-mix(in oklab, var(--accent) 10%, transparent)' : 'transparent',
                borderLeft: active ? '2px solid var(--accent)' : '2px solid transparent',
                animation: active ? 'flashRow 0.6s ease-out' : undefined,
              }}>
                <span style={{ width: 26, color: 'var(--text-mute)' }}>{String(pk.i).padStart(2,'0')}</span>
                <span style={{ width: 56, color }}>{pk.proto}</span>
                <span style={{ flex: 1, color: active ? 'var(--text)' : 'var(--text-dim)' }}>
                  {pk.src}:{pk.sport || '—'} → {pk.dst}:{pk.dport || '—'}
                </span>
                <span style={{ width: 60, textAlign: 'right', color: 'var(--text-dim)' }}>{pk.len}</span>
              </div>
            );
          })}
        </div>

        {/* detail panel */}
        <div style={demoStyles.detailCol}>
          <div style={demoStyles.detailHead}>
            <span className="mono" style={{ fontSize: 10.5, color: 'var(--text-mute)', letterSpacing: '0.1em' }}>FRAME #{p.i}</span>
            <Tag fg={PROTO_COLOR[p.proto]} bg={`color-mix(in oklab, ${PROTO_COLOR[p.proto]} 15%, transparent)`}>{p.proto}</Tag>
            <Tag fg={FLAG_STYLE[p.flag]?.fg || 'var(--text-dim)'} bg={FLAG_STYLE[p.flag]?.bg || 'var(--panel-3)'}>{p.flag}</Tag>
          </div>

          <div style={demoStyles.tree}>
            <TreeLine label="Ethernet II" value={`${p.src.replace(/\..*/,'aa:bb:cc:dd:ee')}… → …`} depth={0}/>
            <TreeLine label="IPv4" value={`${p.src} → ${p.dst}`} depth={1} editable/>
            {p.proto !== 'ICMP' && p.sport > 0 && <TreeLine label={p.proto === 'DNS' ? 'UDP' : 'TCP/UDP'} value={`${p.sport} → ${p.dport}`} depth={2} editable/>}
            {p.sni && <TreeLine label="TLS → SNI" value={p.sni} depth={3} editing/>}
            {p.proto === 'DNS' && <TreeLine label="DNS Query" value={p.info} depth={3}/>}
            {p.proto === 'HTTP' && <TreeLine label="HTTP" value={p.info} depth={3}/>}
          </div>

          <div style={demoStyles.detailFoot}>
            <span className="mono" style={{ fontSize: 11, color: 'var(--text-mute)' }}>
              t = <span style={{ color: 'var(--accent-2)' }}>{p.t.toFixed(6)}s</span> · len <span style={{ color: 'var(--accent-2)' }}>{p.len}b</span>
            </span>
            <span className="mono" style={{ fontSize: 11, color: 'var(--accent)' }}>✓ checksum ok</span>
          </div>
        </div>
      </div>
    </div>
  );
}

function TreeLine({ label, value, depth = 0, editable, editing }) {
  return (
    <div style={{
      display: 'flex', alignItems: 'center', gap: 10,
      paddingLeft: 10 + depth * 14,
      padding: '5px 10px', paddingLeft: 10 + depth * 14,
      borderLeft: editing ? '2px solid var(--accent)' : '2px solid transparent',
      background: editing ? 'color-mix(in oklab, var(--accent) 7%, transparent)' : 'transparent',
      fontSize: 12,
    }}>
      <span style={{ color: 'var(--text-mute)' }}>
        {depth === 0 ? '▸' : '·'.repeat(depth)}
      </span>
      <span style={{ width: 92, color: 'var(--text-dim)' }} className="mono">{label}</span>
      <span className="mono" style={{
        color: editing ? 'var(--accent)' : 'var(--text)',
        background: editable ? 'var(--panel-3)' : 'transparent',
        padding: editable ? '1px 6px' : 0,
        borderRadius: 3,
        border: editable ? '1px solid var(--line)' : 'none',
      }}>
        {value}
        {editing && <span style={{ marginLeft: 2, animation: 'blinkCaret 1s infinite' }}>▍</span>}
      </span>
    </div>
  );
}

const demoStyles = {
  wrap: {
    background: 'var(--panel)',
    border: '1px solid var(--line)',
    borderRadius: 8,
    overflow: 'hidden',
    boxShadow: '0 20px 60px rgba(0,0,0,0.4)',
  },
  windowBar: {
    display: 'flex', alignItems: 'center', gap: 4,
    padding: '8px 12px',
    background: 'var(--panel-2)',
    borderBottom: '1px solid var(--line)',
  },
  dot: { width: 11, height: 11, borderRadius: 11 },
  playBtn: {
    display: 'inline-flex', alignItems: 'center', gap: 4,
    background: 'var(--panel-3)', color: 'var(--text-dim)',
    border: '1px solid var(--line)', borderRadius: 4,
    padding: '2px 8px', fontSize: 11, fontFamily: 'var(--mono)',
  },
  grid: {
    display: 'grid',
    gridTemplateColumns: '1fr 1fr',
  },
  listCol: {
    borderRight: '1px solid var(--line)',
    fontFamily: 'var(--mono)',
    fontSize: 11.5,
  },
  listHead: {
    display: 'flex', gap: 8,
    padding: '8px 12px',
    color: 'var(--text-mute)',
    fontSize: 10.5, letterSpacing: '0.1em',
    borderBottom: '1px solid var(--line)',
    background: 'var(--panel-2)',
  },
  row: {
    display: 'flex', gap: 8,
    padding: '7px 10px',
    paddingLeft: 10,
    transition: 'all 0.2s',
  },
  detailCol: { display: 'flex', flexDirection: 'column' },
  detailHead: {
    display: 'flex', alignItems: 'center', gap: 8,
    padding: '10px 14px',
    background: 'var(--panel-2)',
    borderBottom: '1px solid var(--line)',
  },
  tree: { padding: '10px 4px', flex: 1 },
  detailFoot: {
    display: 'flex', justifyContent: 'space-between',
    padding: '10px 14px',
    borderTop: '1px solid var(--line)',
    background: 'var(--panel-2)',
  },
};

function OverviewView({ onNav }) {
  return (
    <div style={{ maxWidth: 1180, margin: '0 auto', padding: '24px 28px 60px', display: 'flex', flexDirection: 'column', gap: 48 }}>

      {/* HERO */}
      <section style={{ display: 'grid', gridTemplateColumns: '1fr 1.15fr', gap: 32, alignItems: 'center', marginTop: 8 }}>
        <div>
          <div className="mono" style={{ color: 'var(--accent)', fontSize: 11.5, letterSpacing: '0.2em', marginBottom: 14 }}>
            // DEVTOOLBOX v1.0.0
          </div>
          <h1 style={{ fontSize: 46, lineHeight: 1.05, letterSpacing: '-0.03em', margin: 0, fontWeight: 700 }}>
            Inspect packets.<br/>
            Rewrite headers.<br/>
            <span style={{ color: 'var(--accent)' }}>Ship.</span>
          </h1>
          <p style={{ fontSize: 15.5, color: 'var(--text-dim)', lineHeight: 1.55, maxWidth: 480, marginTop: 18 }}>
            A browser-based suite for data-plane engineers. Generate synthetic
            PCAPs, edit captured traffic byte-by-byte, merge sessions, and
            x-ray any binary — all from one window, no install on the client.
          </p>
          <div style={{ display: 'flex', gap: 10, marginTop: 22, flexWrap: 'wrap' }}>
            <button onClick={() => onNav('editor')} style={heroStyles.primary}>
              <IconEditor size={14}/> Open PCAP Editor
            </button>
            <button onClick={() => onNav('usecases')} style={heroStyles.ghost}>
              <IconFlow size={14}/> See workflows
            </button>
            <a className="mono" href="#" style={heroStyles.link}>
              git clone devtoolbox.git →
            </a>
          </div>
          <div style={{ display: 'flex', gap: 18, marginTop: 28, flexWrap: 'wrap' }}>
            <Stat n="7" l="tools"/>
            <Stat n="8" l="protocols" color="var(--accent-2)"/>
            <Stat n="∞" l="file size" color="var(--accent-3)"/>
            <Stat n="MIT" l="license" color="var(--accent-5)"/>
          </div>
        </div>

        <LivePacketDemo/>
      </section>

      {/* TOOL GALLERY */}
      <section>
        <SectionHeading
          kicker="— THE TOOLBELT"
          title="Seven tools, one window."
          desc="Each opens in its own workspace with consistent keyboard shortcuts. Pipe output between tools — generated captures open directly in the editor, modified captures drop into the hex viewer."
        />
        <div style={galleryStyles.grid}>
          {[
            { id:'editor', icon:IconEditor, name:'PCAP Editor', tag:'core', desc:'Inspect & rewrite captures. Edit MACs, IPs, ports, VLAN, DNS, HTTP Host, TLS SNI with auto-checksums.', preview:<EditorPreview/> },
            { id:'generator', icon:IconGenerator, name:'PCAP Generator', desc:'Synthesize traffic with full TCP handshakes, DNS queries, TLS handshakes. 8 protocols, auto-incrementing IPs.', preview:<GenPreview/> },
            { id:'merger', icon:IconMerger, name:'PCAP Merger', desc:'Combine 2+ captures into one. Preserves order and timing. Mixed PCAP/PCAPNG supported.', preview:<MergePreview/> },
            { id:'hex', icon:IconHex, name:'Hex Viewer', desc:'Dual-view binary inspector. Auto-detect JSON/XML/text/binary. Search hex patterns or ASCII.', preview:<HexPreview/> },
            { id:'files', icon:IconFiles, name:'File Manager', desc:'Browse everything in uploads/. Rename, delete, download, or open in any tool.', preview:<FilesPreview/> },
            { id:'pdf', icon:IconPDF, name:'PDF Editor', desc:'Click text in a PDF to edit in place. Preserves font size and position.', preview:<PDFPreview/> },
          ].map(t => (
            <button key={t.id} onClick={() => onNav(t.id)} style={galleryStyles.card}>
              <div style={galleryStyles.cardHead}>
                <div style={galleryStyles.cardIcon}><t.icon size={16}/></div>
                <span style={{ fontWeight: 600, fontSize: 14 }}>{t.name}</span>
                {t.tag && <Tag fg="var(--accent)" bg="color-mix(in oklab, var(--accent) 15%, transparent)">{t.tag}</Tag>}
                <IconChevR size={14} style={{ marginLeft: 'auto', color: 'var(--text-mute)' }}/>
              </div>
              <p style={galleryStyles.cardDesc}>{t.desc}</p>
              <div style={galleryStyles.cardPreview}>{t.preview}</div>
            </button>
          ))}
        </div>
      </section>

      {/* WORKFLOW */}
      <section>
        <SectionHeading
          kicker="— PIPELINES"
          title="Chain tools like Unix pipes."
          desc="Every output opens in the next tool with one click. Three common workflows:"
        />
        <WorkflowDiagram/>
      </section>

      {/* FEATURE GRID */}
      <section>
        <SectionHeading
          kicker="— WHY IT EXISTS"
          title="Wireshark in your browser. Scapy behind the scenes."
        />
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 14 }}>
          {[
            ['Zero install on the client', 'Runs entirely in the browser. Share a link to your teammate; they click and use it.', IconPlay],
            ['Powered by Scapy', 'Same library Wireshark plugin authors use. Full TCP/UDP/DNS/TLS support with correct checksums.', IconGenerator],
            ['Built for data plane', 'VLAN tags, dual-stack IPv4/v6, CIDR, protocol reverse-engineering. Not consumer-grade.', IconEditor],
            ['API-first', '/api/* endpoints exposed. Automate from CI, scripts, or other tools.', IconHex],
            ['Auto-checksum', 'Modify an IP, port, or payload — TCP/UDP/v4/v6 checksums recompute on save.', IconCheck],
            ['Inline editing', 'Click any field in the packet tree to edit. No pop-up modals, no forms.', IconCopy],
          ].map(([t, d, I]) => (
            <div key={t} style={featStyles.card}>
              <div style={featStyles.icon}><I size={14}/></div>
              <div style={{ fontWeight: 600, fontSize: 13.5, marginBottom: 4 }}>{t}</div>
              <div style={{ fontSize: 12.5, color: 'var(--text-dim)', lineHeight: 1.5 }}>{d}</div>
            </div>
          ))}
        </div>
      </section>

      {/* QUICKSTART */}
      <section>
        <SectionHeading
          kicker="— QUICK START"
          title="Running in 5 minutes."
          desc="Python 3.8+ and Node 14+. Two terminals, four commands."
        />
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14 }}>
          <CodeBlock title="Terminal 1 — backend" lines={[
            { c: 'python -m venv .venv', out: null },
            { c: 'source .venv/bin/activate', out: null },
            { c: 'cd backend && pip install -r requirements.txt', out: null },
            { c: 'python app.py', out: '✓ serving at http://localhost:5000' },
          ]}/>
          <CodeBlock title="Terminal 2 — frontend" lines={[
            { c: 'cd frontend', out: null },
            { c: 'npm install', out: null },
            { c: 'npm run dev', out: '✓ local: http://localhost:8080' },
            { c: 'open http://localhost:8080', out: null },
          ]}/>
        </div>
      </section>

    </div>
  );
}

function Stat({ n, l, color = 'var(--accent)' }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column' }}>
      <span className="mono" style={{ fontSize: 22, color, letterSpacing: '-0.02em', fontWeight: 600 }}>{n}</span>
      <span className="mono" style={{ fontSize: 10.5, color: 'var(--text-mute)', letterSpacing: '0.1em' }}>{l}</span>
    </div>
  );
}

function EditorPreview() {
  return (
    <div className="mono" style={{ fontSize: 10, lineHeight: 1.4 }}>
      {[
        ['01', 'TCP', 'SYN', 'var(--accent)'],
        ['02', 'TCP', 'SYN-ACK', 'var(--accent)'],
        ['03', 'TLS', 'Client Hello', 'var(--accent-4)'],
        ['04', 'DNS', 'A record', 'var(--accent-5)'],
      ].map(([i,p,f,c]) => (
        <div key={i} style={{ display: 'flex', gap: 6, padding: '2px 0' }}>
          <span style={{ color: 'var(--text-mute)' }}>{i}</span>
          <span style={{ color: c, width: 34 }}>{p}</span>
          <span style={{ color: 'var(--text-dim)' }}>{f}</span>
        </div>
      ))}
    </div>
  );
}
function GenPreview() {
  return (
    <div className="mono" style={{ fontSize: 10 }}>
      <div style={{ color: 'var(--text-dim)' }}>protocol <span style={{ color: 'var(--accent-2)' }}>tls</span></div>
      <div style={{ color: 'var(--text-dim)' }}>count    <span style={{ color: 'var(--accent-2)' }}>100</span></div>
      <div style={{ color: 'var(--text-dim)' }}>vlan     <span style={{ color: 'var(--accent-2)' }}>2018</span></div>
      <div style={{ color: 'var(--accent)', marginTop: 4 }}>▸ generating…</div>
    </div>
  );
}
function MergePreview() {
  return (
    <div className="mono" style={{ fontSize: 10 }}>
      <div style={{ color: 'var(--text-dim)' }}>a.pcap <span style={{ color: 'var(--text-mute)' }}>24 pkts</span></div>
      <div style={{ color: 'var(--text-dim)' }}>b.pcap <span style={{ color: 'var(--text-mute)' }}>41 pkts</span></div>
      <div style={{ color: 'var(--text-dim)' }}>c.pcap <span style={{ color: 'var(--text-mute)' }}>17 pkts</span></div>
      <div style={{ color: 'var(--accent)', marginTop: 4 }}>→ merged 82 pkts</div>
    </div>
  );
}
function HexPreview() {
  return (
    <div className="mono" style={{ fontSize: 9.5, lineHeight: 1.35 }}>
      <div><span style={{ color: 'var(--text-mute)' }}>0000</span> <span style={{ color: 'var(--accent-2)' }}>89 50 4e 47</span> 0d 0a 1a 0a  .PNG....</div>
      <div><span style={{ color: 'var(--text-mute)' }}>0008</span> 00 00 00 0d 49 48 44 52  ....IHDR</div>
      <div><span style={{ color: 'var(--text-mute)' }}>0010</span> 00 00 04 00 00 00 02 40  .......@</div>
    </div>
  );
}
function FilesPreview() {
  return (
    <div className="mono" style={{ fontSize: 10 }}>
      {['capture_01.pcap','firmware.bin','config.json','audit.pdf'].map(n => (
        <div key={n} style={{ color: 'var(--text-dim)' }}>• {n}</div>
      ))}
    </div>
  );
}
function PDFPreview() {
  return (
    <div className="mono" style={{ fontSize: 10, color: 'var(--text-dim)' }}>
      <div>page 1 of 12</div>
      <div style={{ marginTop: 4 }}>
        "Quarterly <span style={{ background: 'color-mix(in oklab, var(--accent) 25%, transparent)', color: 'var(--accent)' }}>audit▍</span>"
      </div>
    </div>
  );
}

function WorkflowDiagram() {
  const flows = [
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
  ];
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
      {flows.map(f => (
        <div key={f.name} style={wfStyles.row}>
          <div style={wfStyles.name}>{f.name}</div>
          <div style={wfStyles.chain}>
            {f.steps.map((s, i) => (
              <React.Fragment key={i}>
                <div style={{ ...wfStyles.step, borderColor: `color-mix(in oklab, ${s.c} 35%, var(--line))` }}>
                  <span style={{ ...wfStyles.pill, background: `color-mix(in oklab, ${s.c} 15%, transparent)`, color: s.c }}>{s.t}</span>
                  <span className="mono" style={{ fontSize: 11, color: 'var(--text-dim)' }}>{s.d}</span>
                </div>
                {i < f.steps.length - 1 && <span style={{ color: 'var(--text-mute)', fontFamily: 'var(--mono)' }}>│</span>}
              </React.Fragment>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}

function CodeBlock({ title, lines }) {
  return (
    <div style={{ background: 'var(--panel)', border: '1px solid var(--line)', borderRadius: 6, overflow: 'hidden' }}>
      <div style={{ padding: '7px 12px', fontSize: 11.5, color: 'var(--text-dim)', borderBottom: '1px solid var(--line)', background: 'var(--panel-2)', fontFamily: 'var(--mono)' }}>
        $ {title}
      </div>
      <div style={{ padding: 12, fontFamily: 'var(--mono)', fontSize: 12, lineHeight: 1.65 }}>
        {lines.map((l, i) => (
          <div key={i}>
            <div><span style={{ color: 'var(--accent)' }}>$</span> <span>{l.c}</span></div>
            {l.out && <div style={{ color: 'var(--text-mute)' }}>  {l.out}</div>}
          </div>
        ))}
      </div>
    </div>
  );
}

const heroStyles = {
  primary: {
    display: 'inline-flex', alignItems: 'center', gap: 7,
    padding: '10px 16px', fontSize: 13, fontWeight: 600,
    background: 'var(--accent)', color: '#0b0d10',
    border: 'none', borderRadius: 6,
  },
  ghost: {
    display: 'inline-flex', alignItems: 'center', gap: 7,
    padding: '10px 16px', fontSize: 13, fontWeight: 500,
    background: 'transparent', color: 'var(--text)',
    border: '1px solid var(--line-2)', borderRadius: 6,
  },
  link: {
    fontSize: 12, color: 'var(--text-dim)', textDecoration: 'none',
    padding: '10px 4px',
  },
};
const galleryStyles = {
  grid: { display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 12 },
  card: {
    background: 'var(--panel)', border: '1px solid var(--line)',
    borderRadius: 8, padding: 16, textAlign: 'left',
    display: 'flex', flexDirection: 'column', gap: 10,
    color: 'var(--text)', transition: 'border-color 0.15s, transform 0.15s',
    cursor: 'pointer',
  },
  cardHead: { display: 'flex', alignItems: 'center', gap: 8 },
  cardIcon: {
    width: 28, height: 28, borderRadius: 6,
    background: 'var(--panel-3)', border: '1px solid var(--line)',
    display: 'grid', placeItems: 'center', color: 'var(--accent)',
  },
  cardDesc: { fontSize: 12.5, color: 'var(--text-dim)', lineHeight: 1.5, margin: 0, minHeight: 56 },
  cardPreview: {
    background: 'var(--bg)', border: '1px solid var(--line)',
    borderRadius: 5, padding: 10, minHeight: 70,
  },
};
const featStyles = {
  card: {
    background: 'var(--panel)', border: '1px solid var(--line)',
    borderRadius: 6, padding: 14,
  },
  icon: {
    width: 26, height: 26, borderRadius: 5,
    background: 'color-mix(in oklab, var(--accent) 12%, transparent)',
    color: 'var(--accent)',
    display: 'grid', placeItems: 'center', marginBottom: 10,
  },
};
const wfStyles = {
  row: {
    display: 'flex', alignItems: 'center', gap: 16,
    padding: '14px 16px',
    background: 'var(--panel)', border: '1px solid var(--line)', borderRadius: 6,
  },
  name: {
    fontSize: 12, color: 'var(--text-dim)', fontFamily: 'var(--mono)',
    width: 180, letterSpacing: '0.03em',
  },
  chain: { display: 'flex', alignItems: 'center', gap: 10, flex: 1, flexWrap: 'wrap' },
  step: {
    display: 'flex', alignItems: 'center', gap: 10,
    padding: '6px 10px', border: '1px solid var(--line)', borderRadius: 5,
    background: 'var(--panel-2)',
  },
  pill: {
    fontSize: 11, padding: '2px 7px', borderRadius: 3,
    fontFamily: 'var(--mono)', fontWeight: 500,
  },
};

Object.assign(window, { OverviewView });

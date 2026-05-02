/* App shell: left rail + top bar + main canvas */

const NAV_ITEMS = [
  { id: 'overview',   label: 'Overview',       Icon: IconHome,      group: 'start' },
  { id: 'editor',     label: 'PCAP Editor',    Icon: IconEditor,    group: 'tools', badge: 'core' },
  { id: 'generator',  label: 'PCAP Generator', Icon: IconGenerator, group: 'tools' },
  { id: 'merger',     label: 'PCAP Merger',    Icon: IconMerger,    group: 'tools' },
  { id: 'hex',        label: 'Hex Viewer',     Icon: IconHex,       group: 'tools' },
  { id: 'files',      label: 'File Manager',   Icon: IconFiles,     group: 'tools' },
  { id: 'pdf',        label: 'PDF Editor',     Icon: IconPDF,       group: 'tools' },
  { id: 'log',        label: 'Log Analyzer',   Icon: IconLog,       group: 'tools', badge: 'soon' },
  { id: 'usecases',   label: 'Use cases',      Icon: IconUseCases,  group: 'learn' },
];

function LeftRail({ current, onNav }) {
  return (
    <aside style={railStyles.rail}>
      <div style={railStyles.brand}>
        <div style={railStyles.brandMark}>
          <svg width="22" height="22" viewBox="0 0 22 22" fill="none" aria-hidden>
            <path d="M3 5.5 11 2l8 3.5v11L11 20l-8-3.5z" stroke="var(--accent)" strokeWidth="1.4"/>
            <path d="M11 2v18M3 5.5 19 16.5M19 5.5 3 16.5" stroke="var(--accent)" strokeWidth="1" opacity="0.5"/>
          </svg>
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', lineHeight: 1.15 }}>
          <span style={{ fontWeight: 700, letterSpacing: '-0.01em' }}>DevToolBox</span>
          <span className="mono" style={{ fontSize: 10.5, color: 'var(--text-mute)' }}>v1.0.0 · flask+scapy+vue</span>
        </div>
      </div>

      <div style={railStyles.search}>
        <IconSearch size={14} style={{ color: 'var(--text-mute)' }}/>
        <input placeholder="Jump to tool…" style={railStyles.searchInput}/>
        <kbd style={railStyles.kbd}>⌘K</kbd>
      </div>

      <nav style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
        <RailGroup label="START">
          {NAV_ITEMS.filter(n => n.group === 'start').map(n => (
            <RailItem key={n.id} item={n} active={current === n.id} onClick={() => onNav(n.id)} />
          ))}
        </RailGroup>
        <RailGroup label="TOOLS">
          {NAV_ITEMS.filter(n => n.group === 'tools').map(n => (
            <RailItem key={n.id} item={n} active={current === n.id} onClick={() => onNav(n.id)} />
          ))}
        </RailGroup>
        <RailGroup label="LEARN">
          {NAV_ITEMS.filter(n => n.group === 'learn').map(n => (
            <RailItem key={n.id} item={n} active={current === n.id} onClick={() => onNav(n.id)} />
          ))}
        </RailGroup>
      </nav>

      <div style={{ marginTop: 'auto', display: 'flex', flexDirection: 'column', gap: 8 }}>
        <div style={railStyles.status}>
          <span style={railStyles.dot}/>
          <span>backend</span>
          <span className="mono" style={{ marginLeft: 'auto', color: 'var(--text-dim)' }}>:5000</span>
        </div>
        <div style={railStyles.status}>
          <span style={{ ...railStyles.dot, background: 'var(--accent-2)' }}/>
          <span>frontend</span>
          <span className="mono" style={{ marginLeft: 'auto', color: 'var(--text-dim)' }}>:8080</span>
        </div>
        <div className="mono" style={{ fontSize: 10.5, color: 'var(--text-mute)', padding: '8px 10px', borderTop: '1px solid var(--line)' }}>
          MIT · built for data-plane engineers
        </div>
      </div>
    </aside>
  );
}

function RailGroup({ label, children }) {
  return (
    <div style={{ marginBottom: 10 }}>
      <div className="mono" style={{ fontSize: 10, color: 'var(--text-mute)', letterSpacing: '0.15em', padding: '6px 10px 4px' }}>{label}</div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 1 }}>{children}</div>
    </div>
  );
}

function RailItem({ item, active, onClick }) {
  const soon = item.badge === 'soon';
  return (
    <button
      onClick={soon ? undefined : onClick}
      disabled={soon}
      style={{
        ...railStyles.item,
        background: active ? 'color-mix(in oklab, var(--accent) 12%, transparent)' : 'transparent',
        color: active ? 'var(--text)' : soon ? 'var(--text-mute)' : 'var(--text-dim)',
        borderLeft: active ? '2px solid var(--accent)' : '2px solid transparent',
        cursor: soon ? 'not-allowed' : 'pointer',
      }}>
      <item.Icon size={15}/>
      <span style={{ flex: 1, textAlign: 'left' }}>{item.label}</span>
      {item.badge === 'core' && <span style={railStyles.badgeCore}>core</span>}
      {item.badge === 'soon' && <span style={railStyles.badgeSoon}>soon</span>}
    </button>
  );
}

function TopBar({ current }) {
  const crumbs = NAV_ITEMS.find(n => n.id === current);
  return (
    <div style={topStyles.bar}>
      <div style={topStyles.crumbs} className="mono">
        <span style={{ color: 'var(--text-mute)' }}>devtoolbox</span>
        <span style={{ color: 'var(--text-mute)' }}>/</span>
        <span style={{ color: 'var(--text)' }}>{crumbs?.label.toLowerCase().replace(' ', '-')}</span>
      </div>
      <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
        <button style={topStyles.ghostBtn}>
          <IconCopy size={13}/><span>Copy link</span>
        </button>
        <button style={topStyles.ghostBtn}>
          <IconDownload size={13}/><span>Docs</span>
        </button>
        <div style={topStyles.sep}/>
        <button style={topStyles.primaryBtn}>
          <IconPlay size={12}/><span>Try it live</span>
        </button>
      </div>
    </div>
  );
}

const railStyles = {
  rail: {
    position: 'fixed',
    top: 0, left: 0, bottom: 0,
    width: 232,
    background: 'var(--panel)',
    borderRight: '1px solid var(--line)',
    display: 'flex',
    flexDirection: 'column',
    padding: '14px 10px',
    gap: 10,
    zIndex: 5,
  },
  brand: {
    display: 'flex', alignItems: 'center', gap: 10,
    padding: '2px 6px 10px',
    borderBottom: '1px solid var(--line)',
  },
  brandMark: {
    width: 30, height: 30, borderRadius: 6,
    background: 'color-mix(in oklab, var(--accent) 10%, transparent)',
    display: 'grid', placeItems: 'center',
    border: '1px solid color-mix(in oklab, var(--accent) 25%, transparent)',
  },
  search: {
    display: 'flex', alignItems: 'center', gap: 6,
    padding: '6px 8px',
    background: 'var(--panel-2)',
    border: '1px solid var(--line)',
    borderRadius: 6,
  },
  searchInput: {
    flex: 1, background: 'transparent', border: 'none', outline: 'none',
    color: 'var(--text)', fontSize: 12.5, fontFamily: 'inherit',
  },
  kbd: {
    fontFamily: 'var(--mono)', fontSize: 10, padding: '2px 5px',
    background: 'var(--panel-3)', border: '1px solid var(--line)',
    borderRadius: 3, color: 'var(--text-mute)',
  },
  item: {
    display: 'flex', alignItems: 'center', gap: 9,
    padding: '7px 10px', paddingLeft: 8,
    fontSize: 12.8, fontWeight: 500,
    background: 'transparent', border: 'none',
    borderRadius: 4, textAlign: 'left',
    transition: 'background 0.12s, color 0.12s',
  },
  badgeCore: {
    fontFamily: 'var(--mono)', fontSize: 9.5, padding: '1px 5px',
    background: 'color-mix(in oklab, var(--accent) 15%, transparent)',
    color: 'var(--accent)',
    border: '1px solid color-mix(in oklab, var(--accent) 30%, transparent)',
    borderRadius: 3, letterSpacing: '0.08em',
  },
  badgeSoon: {
    fontFamily: 'var(--mono)', fontSize: 9.5, padding: '1px 5px',
    background: 'var(--panel-3)', color: 'var(--text-mute)',
    border: '1px solid var(--line)', borderRadius: 3, letterSpacing: '0.08em',
  },
  status: {
    display: 'flex', alignItems: 'center', gap: 7,
    padding: '6px 10px', fontSize: 11.5, color: 'var(--text-dim)',
    fontFamily: 'var(--mono)',
  },
  dot: {
    width: 7, height: 7, borderRadius: 7, background: 'var(--accent)',
    boxShadow: '0 0 6px var(--accent)',
  },
};

const topStyles = {
  bar: {
    position: 'sticky', top: 0,
    height: 48,
    background: 'color-mix(in oklab, var(--bg) 85%, transparent)',
    backdropFilter: 'blur(8px)',
    borderBottom: '1px solid var(--line)',
    display: 'flex', alignItems: 'center', justifyContent: 'space-between',
    padding: '0 24px',
    zIndex: 3,
  },
  crumbs: { display: 'flex', gap: 6, fontSize: 12 },
  ghostBtn: {
    display: 'inline-flex', alignItems: 'center', gap: 6,
    padding: '6px 10px', fontSize: 12,
    background: 'transparent', color: 'var(--text-dim)',
    border: '1px solid var(--line)', borderRadius: 5,
  },
  primaryBtn: {
    display: 'inline-flex', alignItems: 'center', gap: 6,
    padding: '6px 12px', fontSize: 12, fontWeight: 600,
    background: 'var(--accent)', color: '#0b0d10',
    border: 'none', borderRadius: 5,
  },
  sep: { width: 1, height: 22, background: 'var(--line)', margin: '0 4px' },
};

/* Shared tiny primitives */
function Panel({ title, subtitle, right, children, style, padding = 16 }) {
  return (
    <section style={{
      background: 'var(--panel)',
      border: '1px solid var(--line)',
      borderRadius: 8,
      overflow: 'hidden',
      ...style,
    }}>
      {(title || right) && (
        <header style={{
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          padding: '11px 14px',
          borderBottom: '1px solid var(--line)',
          background: 'var(--panel-2)',
        }}>
          <div>
            {title && <div style={{ fontSize: 13, fontWeight: 600 }}>{title}</div>}
            {subtitle && <div style={{ fontSize: 11.5, color: 'var(--text-dim)', marginTop: 1 }}>{subtitle}</div>}
          </div>
          {right}
        </header>
      )}
      <div style={{ padding }}>{children}</div>
    </section>
  );
}

function Tag({ children, fg = 'var(--text-dim)', bg = 'var(--panel-3)', style }) {
  return (
    <span className="mono" style={{
      display: 'inline-flex', alignItems: 'center',
      fontSize: 10.5, padding: '2px 6px', borderRadius: 3,
      background: bg, color: fg, letterSpacing: '0.03em',
      border: '1px solid color-mix(in oklab, currentColor 15%, transparent)',
      ...style,
    }}>{children}</span>
  );
}

function SectionHeading({ kicker, title, desc, children }) {
  return (
    <div style={{ marginBottom: 18 }}>
      {kicker && (
        <div className="mono" style={{ fontSize: 11, color: 'var(--accent)', letterSpacing: '0.15em', marginBottom: 8 }}>
          {kicker}
        </div>
      )}
      <h2 style={{ fontSize: 26, fontWeight: 700, letterSpacing: '-0.02em', margin: 0 }}>{title}</h2>
      {desc && <p style={{ fontSize: 14, color: 'var(--text-dim)', margin: '8px 0 0', maxWidth: 720 }}>{desc}</p>}
      {children}
    </div>
  );
}

Object.assign(window, { LeftRail, TopBar, Panel, Tag, SectionHeading, NAV_ITEMS });

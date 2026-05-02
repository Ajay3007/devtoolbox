/* PCAP Editor — interactive packet list, detail tree, inline editing */

function PCAPEditorView() {
  const [packets, setPackets] = React.useState(SAMPLE_PACKETS);
  const [selected, setSelected] = React.useState(3);
  const [filter, setFilter] = React.useState('');
  const [protoFilter, setProtoFilter] = React.useState('all');
  const [editingField, setEditingField] = React.useState(null);
  const [editValue, setEditValue] = React.useState('');
  const [flashId, setFlashId] = React.useState(null);
  const [modified, setModified] = React.useState(new Set());
  const [bulk, setBulk] = React.useState(false);
  const [bulkSel, setBulkSel] = React.useState(new Set());

  const filtered = packets.filter(p => {
    if (protoFilter !== 'all' && p.proto !== protoFilter) return false;
    if (!filter) return true;
    const q = filter.toLowerCase();
    return p.src.includes(q) || p.dst.includes(q) || p.info.toLowerCase().includes(q) || String(p.i) === q;
  });

  const sel = packets.find(p => p.i === selected) || packets[0];

  const commitEdit = (field) => {
    setPackets(prev => prev.map(p => p.i === sel.i ? { ...p, [field]: editValue } : p));
    setModified(prev => new Set([...prev, sel.i]));
    setFlashId(sel.i);
    setTimeout(() => setFlashId(null), 700);
    setEditingField(null);
  };

  const startEdit = (field, val) => {
    setEditingField(field);
    setEditValue(val);
  };

  const protos = [...new Set(packets.map(p => p.proto))];

  return (
    <div style={editorStyles.page}>
      <ViewHeader
        icon={IconEditor}
        title="PCAP Editor"
        subtitle="Inspect, filter, and rewrite packets with automatic checksum recalculation."
        actions={[
          { label: 'Upload', icon: IconUpload, ghost: true },
          { label: modified.size ? `Download Modified (${modified.size})` : 'Download PCAP', icon: IconDownload, primary: true },
        ]}
      />

      {/* file bar */}
      <div style={editorStyles.fileBar}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <IconFiles size={14} style={{ color: 'var(--accent-3)' }}/>
          <span className="mono" style={{ fontSize: 12 }}>capture_20260224.pcap</span>
          <Tag>pcap</Tag>
          <Tag fg="var(--text-dim)">{packets.length} packets</Tag>
          <Tag fg="var(--text-dim)">1.4 KB</Tag>
          {modified.size > 0 && <Tag fg="var(--accent-3)" bg="color-mix(in oklab, var(--accent-3) 15%, transparent)">● modified ({modified.size})</Tag>}
        </div>
        <div style={{ display: 'flex', gap: 6 }}>
          <IconButton label="Bulk edit" icon={IconFilter} active={bulk} onClick={() => setBulk(v => !v)}/>
          <IconButton label="Export filtered" icon={IconDownload}/>
        </div>
      </div>

      {/* main grid */}
      <div style={editorStyles.grid}>
        {/* filter rail */}
        <div style={editorStyles.filters}>
          <div style={editorStyles.filterBox}>
            <IconSearch size={13} style={{ color: 'var(--text-mute)' }}/>
            <input
              placeholder="ip, port, info…"
              value={filter}
              onChange={e => setFilter(e.target.value)}
              style={editorStyles.filterInput}
            />
          </div>
          <div style={{ marginTop: 14 }}>
            <div className="mono" style={editorStyles.filterLabel}>PROTOCOL</div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
              <FilterPill label="all" count={packets.length} active={protoFilter==='all'} onClick={() => setProtoFilter('all')} color="var(--text-dim)"/>
              {protos.map(p => (
                <FilterPill key={p} label={p} count={packets.filter(x=>x.proto===p).length}
                  active={protoFilter===p} onClick={() => setProtoFilter(p)}
                  color={PROTO_COLOR[p]}/>
              ))}
            </div>
          </div>
          <div style={{ marginTop: 14 }}>
            <div className="mono" style={editorStyles.filterLabel}>STATISTICS</div>
            <StatLine k="total" v={packets.length}/>
            <StatLine k="tcp" v={packets.filter(p=>p.proto==='TCP').length}/>
            <StatLine k="tls" v={packets.filter(p=>p.proto==='TLS').length}/>
            <StatLine k="dns" v={packets.filter(p=>p.proto==='DNS').length}/>
            <StatLine k="total bytes" v={packets.reduce((s,p)=>s+p.len,0)}/>
          </div>
        </div>

        {/* packet list */}
        <div style={editorStyles.listPane}>
          <div style={editorStyles.listHead}>
            {bulk && <span style={{ width: 24 }}/>}
            <span style={{ width: 30 }}>#</span>
            <span style={{ width: 78 }}>time</span>
            <span style={{ width: 60 }}>proto</span>
            <span style={{ width: 84 }}>flag</span>
            <span style={{ flex: 1 }}>src → dst</span>
            <span style={{ width: 60, textAlign: 'right' }}>len</span>
          </div>
          <div style={editorStyles.listBody}>
            {filtered.map(p => {
              const active = p.i === selected;
              const flash = flashId === p.i;
              const mod = modified.has(p.i);
              const flag = FLAG_STYLE[p.flag];
              return (
                <div key={p.i}
                  onClick={() => setSelected(p.i)}
                  style={{
                    ...editorStyles.listRow,
                    background: active ? 'color-mix(in oklab, var(--accent) 10%, transparent)' : flash ? 'color-mix(in oklab, var(--accent-3) 18%, transparent)' : 'transparent',
                    borderLeft: active ? '2px solid var(--accent)' : mod ? '2px solid var(--accent-3)' : '2px solid transparent',
                  }}>
                  {bulk && (
                    <span style={{ width: 24 }}>
                      <input type="checkbox" checked={bulkSel.has(p.i)}
                        onChange={e => {
                          e.stopPropagation();
                          const next = new Set(bulkSel);
                          next.has(p.i) ? next.delete(p.i) : next.add(p.i);
                          setBulkSel(next);
                        }}/>
                    </span>
                  )}
                  <span style={{ width: 30, color: 'var(--text-mute)' }}>{String(p.i).padStart(2,'0')}</span>
                  <span style={{ width: 78, color: 'var(--text-dim)' }}>{p.t.toFixed(6)}</span>
                  <span style={{ width: 60, color: PROTO_COLOR[p.proto], fontWeight: 500 }}>{p.proto}</span>
                  <span style={{ width: 84 }}>
                    {flag && <span style={{
                      background: flag.bg, color: flag.fg,
                      padding: '1px 6px', fontSize: 10.5, borderRadius: 3,
                    }}>{p.flag}</span>}
                  </span>
                  <span style={{ flex: 1, color: active ? 'var(--text)' : 'var(--text-dim)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    <span>{p.src}{p.sport>0?`:${p.sport}`:''}</span>
                    <span style={{ color: 'var(--text-mute)', margin: '0 5px' }}>→</span>
                    <span>{p.dst}{p.dport>0?`:${p.dport}`:''}</span>
                    <span style={{ color: 'var(--text-mute)', marginLeft: 8 }}>· {p.info}</span>
                  </span>
                  <span style={{ width: 60, textAlign: 'right', color: 'var(--text-dim)' }}>{p.len}</span>
                </div>
              );
            })}
          </div>
        </div>

        {/* detail pane */}
        <div style={editorStyles.detailPane}>
          <div style={editorStyles.detailHead}>
            <span className="mono" style={{ fontSize: 11, color: 'var(--text-mute)', letterSpacing: '0.1em' }}>PACKET #{sel.i}</span>
            <Tag fg={PROTO_COLOR[sel.proto]} bg={`color-mix(in oklab, ${PROTO_COLOR[sel.proto]} 15%, transparent)`}>{sel.proto}</Tag>
            <Tag fg={FLAG_STYLE[sel.flag]?.fg} bg={FLAG_STYLE[sel.flag]?.bg}>{sel.flag}</Tag>
            {modified.has(sel.i) && <Tag fg="var(--accent-3)" bg="color-mix(in oklab, var(--accent-3) 15%, transparent)">● edited</Tag>}
          </div>

          <div style={editorStyles.detailBody}>
            <DetailGroup label="Frame">
              <EditableField k="timestamp" v={sel.t.toFixed(6) + 's'} readOnly/>
              <EditableField k="length" v={`${sel.len} bytes`} readOnly/>
            </DetailGroup>

            <DetailGroup label="Ethernet II" expanded>
              <EditableField k="src mac" v="aa:bb:cc:11:22:33"
                editing={editingField==='src_mac'}
                onEdit={() => startEdit('src_mac','aa:bb:cc:11:22:33')}
                onChange={setEditValue} value={editValue} onCommit={() => commitEdit('src_mac')}/>
              <EditableField k="dst mac" v="dd:ee:ff:44:55:66"
                editing={editingField==='dst_mac'}
                onEdit={() => startEdit('dst_mac','dd:ee:ff:44:55:66')}
                onChange={setEditValue} value={editValue} onCommit={() => commitEdit('dst_mac')}/>
              <EditableField k="vlan id" v="2018" color="var(--accent-5)"
                editing={editingField==='vlan'}
                onEdit={() => startEdit('vlan','2018')}
                onChange={setEditValue} value={editValue} onCommit={() => commitEdit('vlan')}/>
            </DetailGroup>

            <DetailGroup label="IPv4" expanded>
              <EditableField k="src ip" v={sel.src}
                editing={editingField==='src'}
                onEdit={() => startEdit('src', sel.src)}
                onChange={setEditValue} value={editValue} onCommit={() => commitEdit('src')}/>
              <EditableField k="dst ip" v={sel.dst}
                editing={editingField==='dst'}
                onEdit={() => startEdit('dst', sel.dst)}
                onChange={setEditValue} value={editValue} onCommit={() => commitEdit('dst')}/>
              <EditableField k="ttl" v="64" readOnly/>
              <EditableField k="checksum" v="0x4a2f" color="var(--accent)" suffix="✓ auto" readOnly/>
            </DetailGroup>

            {sel.sport > 0 && (
              <DetailGroup label={sel.proto === 'DNS' || sel.layers.includes('UDP') ? 'UDP' : 'TCP'} expanded>
                <EditableField k="src port" v={String(sel.sport)}
                  editing={editingField==='sport'}
                  onEdit={() => startEdit('sport', String(sel.sport))}
                  onChange={setEditValue} value={editValue} onCommit={() => commitEdit('sport')}/>
                <EditableField k="dst port" v={String(sel.dport)}
                  editing={editingField==='dport'}
                  onEdit={() => startEdit('dport', String(sel.dport))}
                  onChange={setEditValue} value={editValue} onCommit={() => commitEdit('dport')}/>
              </DetailGroup>
            )}

            {sel.proto === 'TLS' && sel.sni && (
              <DetailGroup label="TLS" expanded highlight>
                <EditableField k="SNI" v={sel.sni} color="var(--accent-4)"
                  editing={editingField==='sni'}
                  onEdit={() => startEdit('sni', sel.sni)}
                  onChange={setEditValue} value={editValue} onCommit={() => commitEdit('sni')}/>
                <EditableField k="version" v="TLS 1.3" readOnly/>
                <EditableField k="cipher suites" v="13 offered" readOnly/>
              </DetailGroup>
            )}

            {sel.proto === 'HTTP' && (
              <DetailGroup label="HTTP" expanded highlight>
                <EditableField k="host" v="api.example.com"
                  editing={editingField==='host'}
                  onEdit={() => startEdit('host','api.example.com')}
                  onChange={setEditValue} value={editValue} onCommit={() => commitEdit('host')}/>
                <EditableField k="method" v={sel.info.split(' ')[0]} readOnly/>
                <EditableField k="path" v={sel.info.split(' ')[1] || '/'} readOnly/>
              </DetailGroup>
            )}

            {sel.proto === 'DNS' && (
              <DetailGroup label="DNS" expanded highlight>
                <EditableField k="query" v={sel.info.replace(/^A /,'').replace(/ TTL.*/,'')}
                  editing={editingField==='query'}
                  onEdit={() => startEdit('query','api.internal.corp')}
                  onChange={setEditValue} value={editValue} onCommit={() => commitEdit('query')}/>
                <EditableField k="record type" v="A" readOnly/>
              </DetailGroup>
            )}
          </div>

          <div style={editorStyles.hexStrip}>
            <div className="mono" style={{ fontSize: 10.5, color: 'var(--text-mute)', letterSpacing: '0.1em', marginBottom: 6 }}>RAW BYTES · first 64</div>
            <div className="mono" style={{ fontSize: 11, lineHeight: 1.6, color: 'var(--text-dim)' }}>
              {Array.from({ length: 4 }).map((_, row) => (
                <div key={row}>
                  <span style={{ color: 'var(--text-mute)' }}>{String(row*16).padStart(4,'0')}</span>
                  {'  '}
                  {Array.from({ length: 16 }).map((_, col) => {
                    const v = (row*16+col + sel.i*3) & 0xff;
                    return <span key={col} style={{ color: col < 6 ? 'var(--accent-2)' : 'var(--text-dim)' }}> {v.toString(16).padStart(2,'0')}</span>;
                  })}
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function DetailGroup({ label, children, expanded = false, highlight }) {
  const [open, setOpen] = React.useState(expanded);
  return (
    <div style={{
      border: '1px solid var(--line)',
      borderLeft: highlight ? '2px solid var(--accent-4)' : '1px solid var(--line)',
      borderRadius: 5, marginBottom: 8, background: 'var(--panel-2)',
      overflow: 'hidden',
    }}>
      <button onClick={() => setOpen(v => !v)} style={{
        width: '100%', background: 'transparent', border: 'none',
        padding: '7px 10px', display: 'flex', alignItems: 'center', gap: 6,
        color: 'var(--text)', fontFamily: 'var(--mono)', fontSize: 11.5, letterSpacing: '0.08em',
      }}>
        {open ? <IconChevD size={12}/> : <IconChevR size={12}/>}
        <span style={{ textTransform: 'uppercase' }}>{label}</span>
      </button>
      {open && <div style={{ padding: '4px 8px 8px' }}>{children}</div>}
    </div>
  );
}

function EditableField({ k, v, color, readOnly, editing, onEdit, value, onChange, onCommit, suffix }) {
  return (
    <div style={{
      display: 'flex', alignItems: 'center', gap: 10,
      padding: '4px 8px',
      borderRadius: 3,
      background: editing ? 'color-mix(in oklab, var(--accent) 8%, transparent)' : 'transparent',
    }}>
      <span className="mono" style={{ width: 96, fontSize: 11, color: 'var(--text-mute)' }}>{k}</span>
      {editing ? (
        <input
          autoFocus
          value={value}
          onChange={e => onChange(e.target.value)}
          onBlur={onCommit}
          onKeyDown={e => { if (e.key === 'Enter') onCommit(); }}
          className="mono"
          style={{
            flex: 1, background: 'var(--panel-3)',
            border: '1px solid var(--accent)', borderRadius: 3,
            color: 'var(--accent)', padding: '2px 6px', fontSize: 12,
            outline: 'none',
          }}
        />
      ) : (
        <button onClick={readOnly ? undefined : onEdit} style={{
          flex: 1, textAlign: 'left',
          background: 'transparent', border: 'none', padding: '2px 6px',
          borderRadius: 3, fontSize: 12, fontFamily: 'var(--mono)',
          color: color || 'var(--text)',
          cursor: readOnly ? 'default' : 'text',
          borderBottom: readOnly ? 'none' : '1px dashed var(--line-2)',
        }}>{v}</button>
      )}
      {suffix && <span className="mono" style={{ fontSize: 10, color: 'var(--accent)' }}>{suffix}</span>}
    </div>
  );
}

function StatLine({ k, v }) {
  return (
    <div className="mono" style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11.5, padding: '3px 8px', color: 'var(--text-dim)' }}>
      <span>{k}</span><span style={{ color: 'var(--text)' }}>{v}</span>
    </div>
  );
}

function FilterPill({ label, count, active, onClick, color }) {
  return (
    <button onClick={onClick} style={{
      display: 'flex', alignItems: 'center', gap: 8,
      padding: '5px 8px', fontSize: 12, fontFamily: 'var(--mono)',
      background: active ? 'color-mix(in oklab, var(--accent) 10%, transparent)' : 'transparent',
      color: active ? 'var(--text)' : 'var(--text-dim)',
      border: '1px solid ' + (active ? 'color-mix(in oklab, var(--accent) 25%, transparent)' : 'var(--line)'),
      borderRadius: 4,
      textAlign: 'left',
    }}>
      <span style={{ width: 7, height: 7, borderRadius: 7, background: color }}/>
      <span style={{ flex: 1 }}>{label}</span>
      <span style={{ color: 'var(--text-mute)' }}>{count}</span>
    </button>
  );
}

function IconButton({ label, icon: I, onClick, active }) {
  return (
    <button onClick={onClick} style={{
      display: 'inline-flex', alignItems: 'center', gap: 6,
      padding: '6px 10px', fontSize: 11.5,
      background: active ? 'color-mix(in oklab, var(--accent) 12%, transparent)' : 'var(--panel-2)',
      color: active ? 'var(--accent)' : 'var(--text-dim)',
      border: '1px solid ' + (active ? 'color-mix(in oklab, var(--accent) 30%, transparent)' : 'var(--line)'),
      borderRadius: 4,
    }}>
      <I size={13}/>{label}
    </button>
  );
}

function ViewHeader({ icon: I, title, subtitle, actions = [] }) {
  return (
    <div style={{ padding: '20px 28px 16px', display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 20 }}>
      <div style={{ display: 'flex', gap: 14, alignItems: 'flex-start' }}>
        <div style={{
          width: 38, height: 38, borderRadius: 7,
          background: 'color-mix(in oklab, var(--accent) 12%, transparent)',
          border: '1px solid color-mix(in oklab, var(--accent) 25%, transparent)',
          color: 'var(--accent)',
          display: 'grid', placeItems: 'center',
        }}>
          <I size={18}/>
        </div>
        <div>
          <h1 style={{ fontSize: 22, margin: 0, letterSpacing: '-0.01em', fontWeight: 700 }}>{title}</h1>
          <p style={{ fontSize: 13, color: 'var(--text-dim)', margin: '2px 0 0', maxWidth: 640 }}>{subtitle}</p>
        </div>
      </div>
      <div style={{ display: 'flex', gap: 8 }}>
        {actions.map((a, i) => (
          <button key={i} style={{
            display: 'inline-flex', alignItems: 'center', gap: 6,
            padding: '8px 12px', fontSize: 12, fontWeight: 500,
            background: a.primary ? 'var(--accent)' : 'transparent',
            color: a.primary ? '#0b0d10' : 'var(--text-dim)',
            border: a.primary ? 'none' : '1px solid var(--line-2)',
            borderRadius: 5,
          }}>
            {a.icon && <a.icon size={13}/>}
            {a.label}
          </button>
        ))}
      </div>
    </div>
  );
}

const editorStyles = {
  page: { display: 'flex', flexDirection: 'column', height: '100%' },
  fileBar: {
    display: 'flex', justifyContent: 'space-between', alignItems: 'center',
    padding: '10px 28px', borderTop: '1px solid var(--line)', borderBottom: '1px solid var(--line)',
    background: 'var(--panel)',
  },
  grid: {
    display: 'grid',
    gridTemplateColumns: '200px 1fr 400px',
    flex: 1,
    minHeight: 0,
  },
  filters: {
    padding: 14, borderRight: '1px solid var(--line)',
    background: 'var(--panel)',
    overflow: 'auto',
  },
  filterBox: {
    display: 'flex', alignItems: 'center', gap: 6,
    padding: '6px 8px',
    background: 'var(--panel-2)', border: '1px solid var(--line)', borderRadius: 4,
  },
  filterInput: {
    flex: 1, background: 'transparent', border: 'none', outline: 'none',
    color: 'var(--text)', fontSize: 12, fontFamily: 'var(--mono)',
  },
  filterLabel: {
    fontSize: 10, color: 'var(--text-mute)', letterSpacing: '0.15em', marginBottom: 6,
  },
  listPane: {
    display: 'flex', flexDirection: 'column',
    background: 'var(--panel)',
    borderRight: '1px solid var(--line)',
    minWidth: 0,
  },
  listHead: {
    display: 'flex', gap: 10, padding: '10px 14px',
    background: 'var(--panel-2)', borderBottom: '1px solid var(--line)',
    fontFamily: 'var(--mono)', fontSize: 10.5, color: 'var(--text-mute)',
    letterSpacing: '0.1em',
  },
  listBody: { overflow: 'auto', flex: 1 },
  listRow: {
    display: 'flex', alignItems: 'center', gap: 10,
    padding: '7px 14px',
    fontFamily: 'var(--mono)', fontSize: 11.5,
    borderBottom: '1px solid color-mix(in oklab, var(--line) 50%, transparent)',
    cursor: 'pointer',
  },
  detailPane: {
    background: 'var(--panel)',
    overflow: 'auto',
    display: 'flex', flexDirection: 'column',
  },
  detailHead: {
    display: 'flex', alignItems: 'center', gap: 8,
    padding: '14px 16px',
    borderBottom: '1px solid var(--line)',
    background: 'var(--panel-2)',
  },
  detailBody: { padding: 12 },
  hexStrip: {
    margin: '0 12px 12px',
    padding: 10,
    background: 'var(--bg)',
    border: '1px solid var(--line)',
    borderRadius: 5,
  },
};

Object.assign(window, { PCAPEditorView, ViewHeader, IconButton, DetailGroup, EditableField });

/* File Manager */

function FilesView() {
  const [selected, setSelected] = React.useState(null);
  const [filter, setFilter] = React.useState('all');

  const filtered = UPLOAD_FILES.filter(f => filter === 'all' || f.type === filter);
  const typeColors = {
    pcap: 'var(--accent)',
    bin:  'var(--accent-2)',
    json: 'var(--accent-5)',
    pdf:  'var(--accent-3)',
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <ViewHeader
        icon={IconFiles}
        title="File Manager"
        subtitle="Everything in uploads/ in one place. Rename, delete, or open any file in its matching tool."
      />
      <div style={{
        display: 'flex', justifyContent: 'space-between',
        padding: '10px 28px', borderTop: '1px solid var(--line)', borderBottom: '1px solid var(--line)',
      }}>
        <div style={{ display: 'flex', gap: 4 }}>
          {['all','pcap','bin','json','pdf'].map(t => (
            <button key={t} onClick={() => setFilter(t)} style={{
              padding: '5px 10px', fontSize: 11.5, fontFamily: 'var(--mono)',
              background: filter === t ? 'color-mix(in oklab, var(--accent) 12%, transparent)' : 'transparent',
              color: filter === t ? 'var(--accent)' : 'var(--text-dim)',
              border: '1px solid ' + (filter === t ? 'color-mix(in oklab, var(--accent) 30%, transparent)' : 'var(--line)'),
              borderRadius: 3,
            }}>{t}</button>
          ))}
        </div>
        <div className="mono" style={{ fontSize: 11.5, color: 'var(--text-dim)' }}>
          {filtered.length} files · {(filtered.reduce((s,f)=>s+f.size,0)/1024).toFixed(1)} KB total
        </div>
      </div>

      <div style={{ flex: 1, overflow: 'auto', padding: '18px 28px 28px', display: 'grid', gridTemplateColumns: '1.4fr 1fr', gap: 18 }}>
        <Panel title="Files" padding={0}>
          <div style={{ display: 'flex', flexDirection: 'column' }}>
            <div style={{
              display: 'grid', gridTemplateColumns: '24px 1fr 70px 100px 100px',
              gap: 10, padding: '9px 14px', background: 'var(--panel-2)',
              borderBottom: '1px solid var(--line)',
              fontFamily: 'var(--mono)', fontSize: 10.5, color: 'var(--text-mute)',
              letterSpacing: '0.1em',
            }}>
              <span></span><span>name</span><span>type</span><span>size</span><span>modified</span>
            </div>
            {filtered.map((f, i) => (
              <div key={f.name} onClick={() => setSelected(f)} style={{
                display: 'grid', gridTemplateColumns: '24px 1fr 70px 100px 100px',
                gap: 10, padding: '10px 14px',
                borderBottom: '1px solid color-mix(in oklab, var(--line) 50%, transparent)',
                cursor: 'pointer',
                background: selected?.name === f.name ? 'color-mix(in oklab, var(--accent) 8%, transparent)' : 'transparent',
                fontFamily: 'var(--mono)', fontSize: 11.5,
              }}>
                <IconFiles size={13} style={{ color: typeColors[f.type] || 'var(--text-mute)' }}/>
                <span style={{ color: selected?.name === f.name ? 'var(--text)' : 'var(--text-dim)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{f.name}</span>
                <span><Tag fg={typeColors[f.type]} bg={`color-mix(in oklab, ${typeColors[f.type]} 15%, transparent)`}>{f.type}</Tag></span>
                <span style={{ color: 'var(--text-dim)' }}>{(f.size/1024).toFixed(1)} KB</span>
                <span style={{ color: 'var(--text-mute)' }}>{f.date}</span>
              </div>
            ))}
          </div>
        </Panel>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          {selected ? (
            <>
              <Panel title="Selected file">
                <div className="mono" style={{ fontSize: 12, color: 'var(--text-dim)', lineHeight: 1.9 }}>
                  name   <span style={{ color: 'var(--text)' }}>{selected.name}</span><br/>
                  type   <span style={{ color: typeColors[selected.type] }}>{selected.type}</span><br/>
                  size   <span style={{ color: 'var(--text)' }}>{selected.size.toLocaleString()} bytes</span><br/>
                  path   <span style={{ color: 'var(--text)' }}>uploads/{selected.name}</span><br/>
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8, marginTop: 14 }}>
                  {selected.type === 'pcap' && <>
                    <button style={btnStyles.primary}><IconEditor size={13}/>Open in Editor</button>
                    <button style={btnStyles.ghost}><IconMerger size={13}/>Add to Merge</button>
                  </>}
                  {(selected.type === 'bin' || selected.type === 'json') && (
                    <button style={btnStyles.primary}><IconHex size={13}/>Open in Hex</button>
                  )}
                  {selected.type === 'pdf' && (
                    <button style={btnStyles.primary}><IconPDF size={13}/>Open in PDF Editor</button>
                  )}
                  <button style={btnStyles.ghost}><IconDownload size={13}/>Download</button>
                </div>
              </Panel>
              <Panel title="Danger zone">
                <div style={{ display: 'flex', gap: 8 }}>
                  <button style={{ ...btnStyles.ghost, flex: 1 }}>Rename</button>
                  <button style={{ ...btnStyles.ghost, flex: 1, color: 'var(--accent-4)', borderColor: 'color-mix(in oklab, var(--accent-4) 25%, transparent)' }}>Delete</button>
                </div>
              </Panel>
            </>
          ) : (
            <Panel title="Details">
              <div style={{ padding: 28, textAlign: 'center', color: 'var(--text-mute)', fontSize: 12.5 }}>
                <IconFiles size={24} style={{ opacity: 0.4, marginBottom: 10 }}/>
                <div>Select a file to see details</div>
              </div>
            </Panel>
          )}
        </div>
      </div>
    </div>
  );
}

Object.assign(window, { FilesView });

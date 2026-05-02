/* PCAP Merger — multi-file drop zone */

function PCAPMergerView() {
  const [files, setFiles] = React.useState([
    { name: 'morning_session.pcap', size: 41_218, packets: 124, protocol: 'mixed' },
    { name: 'afternoon_session.pcap', size: 28_004, packets: 88, protocol: 'TCP/TLS' },
  ]);
  const [outname, setOutname] = React.useState('merged_session_20260424.pcap');
  const [merged, setMerged] = React.useState(false);

  const available = [
    { name: 'generated_tcp_10pkts_20260224.pcap', size: 712, packets: 10 },
    { name: 'generated_dns_udp_vlan2008_1pkts.pcap', size: 128, packets: 1 },
    { name: 'evening_capture.pcap', size: 52_800, packets: 164 },
  ];

  const totalPackets = files.reduce((s,f) => s + f.packets, 0);
  const totalSize = files.reduce((s,f) => s + f.size, 0);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <ViewHeader
        icon={IconMerger}
        title="PCAP Merger"
        subtitle="Combine multiple PCAP/PCAPNG files into one. Timing and order preserved."
      />
      <div style={{ padding: '8px 28px 28px', display: 'grid', gridTemplateColumns: '1.2fr 1fr', gap: 18, flex: 1, minHeight: 0, overflow: 'auto' }}>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          <Panel title="Input files" subtitle={`${files.length} queued · merge requires 2+`}>
            <div style={{
              border: '2px dashed var(--line-2)', borderRadius: 6,
              padding: 18, textAlign: 'center', marginBottom: 12,
              background: 'var(--bg)',
            }}>
              <IconUpload size={22} style={{ color: 'var(--text-mute)', marginBottom: 8 }}/>
              <div style={{ fontSize: 13, color: 'var(--text-dim)' }}>Drop PCAP/PCAPNG files or click to browse</div>
              <div className="mono" style={{ fontSize: 11, color: 'var(--text-mute)', marginTop: 4 }}>or pick from uploads/ below</div>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
              {files.map((f, i) => (
                <div key={f.name} style={{
                  display: 'flex', alignItems: 'center', gap: 10,
                  padding: '10px 12px',
                  background: 'var(--panel-2)', border: '1px solid var(--line)', borderRadius: 5,
                }}>
                  <span className="mono" style={{ fontSize: 10.5, color: 'var(--text-mute)', width: 22 }}>{String(i+1).padStart(2,'0')}</span>
                  <IconFiles size={13} style={{ color: 'var(--accent-3)' }}/>
                  <span className="mono" style={{ fontSize: 12, flex: 1 }}>{f.name}</span>
                  <Tag>{f.protocol || 'mixed'}</Tag>
                  <span className="mono" style={{ fontSize: 11, color: 'var(--text-dim)' }}>{f.packets} pkts</span>
                  <span className="mono" style={{ fontSize: 11, color: 'var(--text-mute)' }}>{(f.size/1024).toFixed(1)} KB</span>
                  <button onClick={() => setFiles(files.filter((_,j) => j !== i))}
                    style={{ background: 'transparent', border: 'none', color: 'var(--text-mute)', padding: 2 }}>
                    <IconX size={13}/>
                  </button>
                </div>
              ))}
            </div>
          </Panel>

          <Panel title="From uploads/" subtitle="Add existing files without re-uploading">
            <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
              {available.map(f => {
                const added = files.some(x => x.name === f.name);
                return (
                  <div key={f.name} style={{
                    display: 'flex', alignItems: 'center', gap: 10,
                    padding: '7px 10px',
                    borderRadius: 4,
                  }}>
                    <IconFiles size={12} style={{ color: 'var(--text-mute)' }}/>
                    <span className="mono" style={{ fontSize: 11.5, flex: 1, color: 'var(--text-dim)' }}>{f.name}</span>
                    <span className="mono" style={{ fontSize: 11, color: 'var(--text-mute)' }}>{f.packets} pkts</span>
                    <button
                      disabled={added}
                      onClick={() => setFiles([...files, {...f, protocol: 'mixed'}])}
                      style={{
                        padding: '3px 8px', fontSize: 11, fontFamily: 'var(--mono)',
                        background: added ? 'transparent' : 'var(--panel-3)',
                        color: added ? 'var(--text-mute)' : 'var(--accent)',
                        border: '1px solid ' + (added ? 'var(--line)' : 'color-mix(in oklab, var(--accent) 25%, transparent)'),
                        borderRadius: 3, cursor: added ? 'default' : 'pointer',
                      }}>
                      {added ? '✓ added' : '+ add'}
                    </button>
                  </div>
                );
              })}
            </div>
          </Panel>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          <Panel title="Output" subtitle="Merged file configuration">
            <Field label="output filename" value={outname} onChange={setOutname}/>
            <div style={{ marginTop: 12, display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
              <MiniStat label="sources" value={files.length}/>
              <MiniStat label="total packets" value={totalPackets.toLocaleString()} color="var(--accent)"/>
              <MiniStat label="est. size" value={(totalSize/1024).toFixed(1) + ' KB'}/>
              <MiniStat label="ordering" value="chronological"/>
            </div>

            <button onClick={() => setMerged(true)} disabled={files.length < 2}
              style={{
                width: '100%', marginTop: 14, padding: '11px 16px', fontSize: 13, fontWeight: 600,
                background: files.length < 2 ? 'var(--panel-3)' : 'var(--accent)',
                color: files.length < 2 ? 'var(--text-mute)' : '#0b0d10',
                border: 'none', borderRadius: 6,
                display: 'inline-flex', alignItems: 'center', justifyContent: 'center', gap: 7,
                cursor: files.length < 2 ? 'not-allowed' : 'pointer',
              }}>
              <IconMerger size={14}/> Merge {files.length} file{files.length === 1 ? '' : 's'}
            </button>
          </Panel>

          {merged && (
            <Panel title="Merge complete">
              <div style={{
                padding: '12px 14px',
                background: 'color-mix(in oklab, var(--accent) 8%, transparent)',
                border: '1px solid color-mix(in oklab, var(--accent) 25%, transparent)',
                borderRadius: 5, marginBottom: 12,
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
                  <IconCheck size={15} style={{ color: 'var(--accent)' }}/>
                  <span className="mono" style={{ fontSize: 12 }}>{outname}</span>
                </div>
                <div className="mono" style={{ fontSize: 11, color: 'var(--text-dim)' }}>
                  {totalPackets} packets · {(totalSize/1024).toFixed(1)} KB · saved to uploads/
                </div>
              </div>
              <div style={{ display: 'flex', gap: 8 }}>
                <button style={{ ...btnStyles.primary, flex: 1 }}><IconDownload size={13}/> Download</button>
                <button style={{ ...btnStyles.ghost, flex: 1 }}><IconEditor size={13}/> Open in Editor</button>
              </div>
            </Panel>
          )}

          <Panel title="Timeline preview" subtitle="How packets interleave">
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {files.map((f, i) => (
                <div key={f.name}>
                  <div className="mono" style={{ fontSize: 11, color: 'var(--text-dim)', marginBottom: 4 }}>{f.name}</div>
                  <div style={{ position: 'relative', height: 14, background: 'var(--panel-3)', borderRadius: 2, overflow: 'hidden' }}>
                    {Array.from({length: Math.min(f.packets, 40)}).map((_, j) => (
                      <div key={j} style={{
                        position: 'absolute',
                        left: (j/40*100) + '%',
                        top: 0, bottom: 0,
                        width: 2,
                        background: [
                          'var(--accent)', 'var(--accent-2)', 'var(--accent-4)', 'var(--accent-5)',
                        ][i % 4],
                        opacity: 0.7,
                      }}/>
                    ))}
                  </div>
                </div>
              ))}
              {merged && (
                <div>
                  <div className="mono" style={{ fontSize: 11, color: 'var(--accent)', marginBottom: 4 }}>→ merged output</div>
                  <div style={{ position: 'relative', height: 14, background: 'var(--panel-3)', borderRadius: 2, overflow: 'hidden' }}>
                    {Array.from({length: 60}).map((_, j) => (
                      <div key={j} style={{
                        position: 'absolute', left: (j/60*100) + '%', top: 0, bottom: 0, width: 2,
                        background: ['var(--accent)','var(--accent-2)','var(--accent-4)','var(--accent-5)'][j % 4],
                      }}/>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </Panel>
        </div>
      </div>
    </div>
  );
}

function MiniStat({ label, value, color = 'var(--text)' }) {
  return (
    <div style={{
      padding: '10px 12px', background: 'var(--panel-2)',
      border: '1px solid var(--line)', borderRadius: 4,
    }}>
      <div className="mono" style={{ fontSize: 10, color: 'var(--text-mute)', letterSpacing: '0.1em', marginBottom: 4 }}>
        {label.toUpperCase()}
      </div>
      <div className="mono" style={{ fontSize: 16, color, fontWeight: 600 }}>{value}</div>
    </div>
  );
}

Object.assign(window, { PCAPMergerView, MiniStat });

/* Hex Viewer — dual pane, search, pagination */

function HexView() {
  const [view, setView] = React.useState('hex');
  const [search, setSearch] = React.useState('');
  const [page, setPage] = React.useState(0);
  const bytesPerPage = 128;
  const total = HEX_BYTES.length;
  const totalPages = Math.ceil(total / bytesPerPage);
  const pageBytes = HEX_BYTES.slice(page * bytesPerPage, (page + 1) * bytesPerPage);

  const searchHits = React.useMemo(() => {
    if (!search) return [];
    const hits = [];
    const q = search.toLowerCase();
    for (let i = 0; i < HEX_BYTES.length - q.length; i++) {
      const str = HEX_BYTES.slice(i, i + q.length).map(b => String.fromCharCode(b)).join('').toLowerCase();
      if (str === q) hits.push(i);
    }
    return hits;
  }, [search]);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <ViewHeader
        icon={IconHex}
        title="Hex Viewer"
        subtitle="Inspect any binary. Auto-detects JSON, XML, text, and binary."
      />

      <div style={{
        display: 'flex', justifyContent: 'space-between', alignItems: 'center',
        padding: '10px 28px', borderTop: '1px solid var(--line)', borderBottom: '1px solid var(--line)',
        background: 'var(--panel)',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <IconFiles size={14} style={{ color: 'var(--accent-2)' }}/>
          <span className="mono" style={{ fontSize: 12 }}>firmware_rtr_edge_v3411.bin</span>
          <Tag fg="var(--text-dim)">{total} bytes</Tag>
          <Tag fg="var(--accent-2)" bg="color-mix(in oklab, var(--accent-2) 15%, transparent)">BINARY</Tag>
          <Tag fg="var(--text-dim)">offset 0x0000</Tag>
        </div>
        <div style={{ display: 'flex', gap: 4 }}>
          <button onClick={() => setView('text')} style={{ ...toggleBtn(view==='text') }}>Text</button>
          <button onClick={() => setView('hex')} style={{ ...toggleBtn(view==='hex') }}>Hex</button>
          <button onClick={() => setView('split')} style={{ ...toggleBtn(view==='split') }}>Split</button>
        </div>
      </div>

      <div style={{
        display: 'flex', justifyContent: 'space-between', alignItems: 'center',
        padding: '8px 28px', borderBottom: '1px solid var(--line)',
      }}>
        <div style={{
          display: 'flex', alignItems: 'center', gap: 7,
          padding: '5px 10px', background: 'var(--panel-2)',
          border: '1px solid var(--line)', borderRadius: 4, width: 340,
        }}>
          <IconSearch size={13} style={{ color: 'var(--text-mute)' }}/>
          <input
            placeholder="search ascii or 0xDE AD BE EF"
            value={search}
            onChange={e => setSearch(e.target.value)}
            className="mono"
            style={{
              flex: 1, background: 'transparent', border: 'none', outline: 'none',
              color: 'var(--text)', fontSize: 12,
            }}
          />
          {searchHits.length > 0 && (
            <span className="mono" style={{ fontSize: 11, color: 'var(--accent)' }}>{searchHits.length} hits</span>
          )}
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <button onClick={() => setPage(Math.max(0, page-1))} style={pagBtn}>◀</button>
          <span className="mono" style={{ fontSize: 11.5, color: 'var(--text-dim)' }}>
            page {page+1} / {totalPages}
          </span>
          <button onClick={() => setPage(Math.min(totalPages-1, page+1))} style={pagBtn}>▶</button>
          <div style={{ width: 1, height: 18, background: 'var(--line)', margin: '0 4px' }}/>
          <button style={{ ...btnStyles.ghost, padding: '5px 10px' }}><IconCopy size={12}/>Copy</button>
          <button style={{ ...btnStyles.ghost, padding: '5px 10px' }}><IconDownload size={12}/>Export</button>
        </div>
      </div>

      <div style={{ flex: 1, overflow: 'auto', padding: '18px 28px 28px' }}>
        {view === 'hex' && <HexDump bytes={pageBytes} startOffset={page * bytesPerPage} searchHits={searchHits}/>}
        {view === 'text' && <TextView bytes={HEX_BYTES}/>}
        {view === 'split' && (
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14 }}>
            <HexDump bytes={pageBytes} startOffset={page * bytesPerPage} searchHits={searchHits}/>
            <TextView bytes={HEX_BYTES}/>
          </div>
        )}
      </div>
    </div>
  );
}

function HexDump({ bytes, startOffset, searchHits }) {
  const rows = [];
  for (let i = 0; i < bytes.length; i += 16) {
    rows.push(bytes.slice(i, i + 16));
  }
  return (
    <div className="mono" style={{
      background: 'var(--bg)', border: '1px solid var(--line)',
      borderRadius: 5, padding: 14,
      fontSize: 12, lineHeight: 1.75, fontFamily: 'var(--mono)',
    }}>
      <div style={{ display: 'flex', gap: 14, color: 'var(--text-mute)', fontSize: 10.5, letterSpacing: '0.1em', borderBottom: '1px solid var(--line)', paddingBottom: 6, marginBottom: 8 }}>
        <span style={{ width: 56 }}>offset</span>
        <span style={{ width: 340 }}>00 01 02 03  04 05 06 07  08 09 0a 0b  0c 0d 0e 0f</span>
        <span>ascii</span>
      </div>
      {rows.map((row, i) => {
        const offset = startOffset + i * 16;
        return (
          <div key={i} style={{ display: 'flex', gap: 14 }}>
            <span style={{ width: 56, color: 'var(--text-mute)' }}>
              {offset.toString(16).padStart(8, '0')}
            </span>
            <span style={{ width: 340 }}>
              {row.map((b, j) => {
                const absOffset = offset + j;
                const isHit = searchHits.some(h => absOffset >= h && absOffset < h + (b.toString().length));
                const isPrintable = b >= 0x20 && b < 0x7f;
                return (
                  <span key={j} style={{
                    color: isHit ? 'var(--accent)' : isPrintable ? 'var(--accent-2)' : 'var(--text-dim)',
                    background: isHit ? 'color-mix(in oklab, var(--accent) 20%, transparent)' : 'transparent',
                    padding: isHit ? '0 1px' : 0,
                  }}>
                    {b.toString(16).padStart(2, '0')}{j === 3 || j === 7 || j === 11 ? '  ' : ' '}
                  </span>
                );
              })}
            </span>
            <span style={{ color: 'var(--text-dim)' }}>
              {row.map((b, j) => {
                const absOffset = offset + j;
                const isHit = searchHits.some(h => absOffset >= h && absOffset < h + 1);
                const char = (b >= 0x20 && b < 0x7f) ? String.fromCharCode(b) : '.';
                return <span key={j} style={{
                  color: isHit ? 'var(--accent)' : (b >= 0x20 && b < 0x7f) ? 'var(--text)' : 'var(--text-mute)',
                  background: isHit ? 'color-mix(in oklab, var(--accent) 20%, transparent)' : 'transparent',
                }}>{char}</span>;
              })}
            </span>
          </div>
        );
      })}
    </div>
  );
}

function TextView({ bytes }) {
  const text = bytes.map(b => (b >= 0x20 && b < 0x7f) || b === 0x0a ? String.fromCharCode(b) : '·').join('');
  return (
    <pre className="mono" style={{
      background: 'var(--bg)', border: '1px solid var(--line)',
      borderRadius: 5, padding: 14,
      fontSize: 12.5, lineHeight: 1.7, color: 'var(--text-dim)',
      margin: 0, whiteSpace: 'pre-wrap', wordBreak: 'break-all',
      maxHeight: 520, overflow: 'auto',
    }}>{text}</pre>
  );
}

const toggleBtn = (active) => ({
  padding: '5px 12px', fontSize: 11.5, fontFamily: 'var(--mono)',
  background: active ? 'color-mix(in oklab, var(--accent) 12%, transparent)' : 'var(--panel-2)',
  color: active ? 'var(--accent)' : 'var(--text-dim)',
  border: '1px solid ' + (active ? 'color-mix(in oklab, var(--accent) 30%, transparent)' : 'var(--line)'),
  borderRadius: 3,
});
const pagBtn = {
  width: 24, height: 24, padding: 0, fontSize: 10,
  background: 'var(--panel-2)', color: 'var(--text-dim)',
  border: '1px solid var(--line)', borderRadius: 3,
};

Object.assign(window, { HexView });

/* PDF Editor — click text to edit in place */

function PDFView() {
  const [editing, setEditing] = React.useState(null);
  const [values, setValues] = React.useState({
    title: 'Q1 2026 Network Audit',
    subtitle: 'Data-plane operations — edge fleet',
    author: 'N. Ops Team',
    intro: 'This report covers packet-level anomalies observed on the rtr-edge fleet during Q1 2026.',
    finding1: 'Unexpected SNI values in 3.2% of outbound TLS flows',
    finding2: 'Elevated ICMP echo rate on VLAN 2018 (subnet 10.0.2.0/24)',
  });

  const update = (k, v) => setValues({ ...values, [k]: v });

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <ViewHeader
        icon={IconPDF}
        title="PDF Editor"
        subtitle="Click any text to edit in place. Font size and positioning are preserved."
      />

      <div style={{
        display: 'flex', justifyContent: 'space-between',
        padding: '10px 28px', borderTop: '1px solid var(--line)', borderBottom: '1px solid var(--line)',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <IconFiles size={14} style={{ color: 'var(--accent-3)' }}/>
          <span className="mono" style={{ fontSize: 12 }}>audit_report_q1.pdf</span>
          <Tag>page 1 / 12</Tag>
        </div>
        <div style={{ display: 'flex', gap: 6 }}>
          <button style={{ ...btnStyles.ghost, padding: '5px 10px' }}>◀ prev</button>
          <button style={{ ...btnStyles.ghost, padding: '5px 10px' }}>next ▶</button>
          <button style={{ ...btnStyles.primary, padding: '5px 12px' }}><IconDownload size={12}/>Save PDF</button>
        </div>
      </div>

      <div style={{ flex: 1, overflow: 'auto', background: '#1d2126', padding: '28px', display: 'flex', justifyContent: 'center' }}>
        {/* fake PDF page */}
        <div style={{
          width: 620, background: '#f3eede', color: '#1a1814',
          borderRadius: 2, boxShadow: '0 20px 60px rgba(0,0,0,0.5)',
          padding: '60px 68px',
          fontFamily: 'Georgia, serif',
          position: 'relative',
        }}>
          <div style={{ fontSize: 10, color: '#8a7f6a', letterSpacing: '0.2em', marginBottom: 8 }}>INTERNAL DOCUMENT</div>
          <EditableText val={values.title} onCommit={v=>update('title',v)}
            style={{ fontSize: 30, fontWeight: 700, lineHeight: 1.15, marginBottom: 6 }}
            editing={editing==='title'} setEditing={v=>setEditing(v?'title':null)}/>
          <EditableText val={values.subtitle} onCommit={v=>update('subtitle',v)}
            style={{ fontSize: 16, fontStyle: 'italic', color: '#5a5042', marginBottom: 40 }}
            editing={editing==='subtitle'} setEditing={v=>setEditing(v?'subtitle':null)}/>

          <div style={{ fontSize: 11, color: '#8a7f6a', letterSpacing: '0.15em', marginBottom: 4 }}>AUTHOR</div>
          <EditableText val={values.author} onCommit={v=>update('author',v)}
            style={{ fontSize: 14, marginBottom: 28 }}
            editing={editing==='author'} setEditing={v=>setEditing(v?'author':null)}/>

          <div style={{ borderTop: '1px solid #c9bfa4', margin: '20px 0' }}/>

          <div style={{ fontSize: 14, fontWeight: 700, marginBottom: 10 }}>1. Executive Summary</div>
          <EditableText val={values.intro} onCommit={v=>update('intro',v)}
            style={{ fontSize: 13, lineHeight: 1.65, marginBottom: 20 }}
            multiline
            editing={editing==='intro'} setEditing={v=>setEditing(v?'intro':null)}/>

          <div style={{ fontSize: 14, fontWeight: 700, marginBottom: 10 }}>2. Key Findings</div>
          <ul style={{ fontSize: 13, lineHeight: 1.8, paddingLeft: 20, color: '#2a2620' }}>
            <li>
              <EditableText val={values.finding1} onCommit={v=>update('finding1',v)}
                style={{ fontSize: 13 }}
                editing={editing==='f1'} setEditing={v=>setEditing(v?'f1':null)}/>
            </li>
            <li>
              <EditableText val={values.finding2} onCommit={v=>update('finding2',v)}
                style={{ fontSize: 13 }}
                editing={editing==='f2'} setEditing={v=>setEditing(v?'f2':null)}/>
            </li>
          </ul>

          <div style={{ position: 'absolute', bottom: 24, right: 68, fontSize: 10, color: '#8a7f6a' }}>page 1</div>
        </div>
      </div>
    </div>
  );
}

function EditableText({ val, onCommit, style, editing, setEditing, multiline }) {
  const [local, setLocal] = React.useState(val);
  React.useEffect(() => setLocal(val), [val]);
  if (editing) {
    const Tag = multiline ? 'textarea' : 'input';
    return (
      <Tag
        autoFocus
        value={local}
        onChange={e => setLocal(e.target.value)}
        onBlur={() => { onCommit(local); setEditing(false); }}
        onKeyDown={e => { if (!multiline && e.key === 'Enter') { onCommit(local); setEditing(false); } }}
        style={{
          ...style,
          width: '100%',
          fontFamily: 'inherit',
          background: 'rgba(124, 249, 164, 0.2)',
          border: '2px solid #3a8a52',
          outline: 'none',
          padding: '2px 4px',
          margin: '-2px -4px',
          boxSizing: 'border-box',
          borderRadius: 2,
          color: 'inherit',
          resize: multiline ? 'vertical' : 'none',
          minHeight: multiline ? 60 : undefined,
        }}
      />
    );
  }
  return (
    <span
      onClick={() => setEditing(true)}
      style={{
        ...style,
        display: 'inline-block',
        cursor: 'text',
        borderBottom: '1px dashed transparent',
        transition: 'background 0.1s',
      }}
      onMouseEnter={e => e.currentTarget.style.background = 'rgba(124, 249, 164, 0.15)'}
      onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
    >
      {val}
    </span>
  );
}

Object.assign(window, { PDFView });

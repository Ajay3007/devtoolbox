/* Use cases / personas */

function UseCasesView() {
  const cases = [
    {
      persona: 'Network Forensics Analyst',
      icon: IconEditor,
      color: 'var(--accent)',
      problem: 'Evidence PCAP from an intrusion — need to redact PII but preserve protocol correctness for court.',
      flow: ['Load capture', 'Bulk-rewrite IPs & SNI', 'Auto-checksum', 'Export sanitized'],
      tools: ['editor'],
      quote: 'Half my day used to be scripting scapy for trivial rewrites. Now a junior can do it.',
    },
    {
      persona: 'Data-plane QA Engineer',
      icon: IconGenerator,
      color: 'var(--accent-2)',
      problem: 'Need 10k synthetic flows across 40 VLANs to stress-test a new packet-processing pipeline.',
      flow: ['Generate per-VLAN captures', 'Merge into one PCAP', 'Replay with tcpreplay'],
      tools: ['generator', 'merger'],
      quote: 'Matrix-testing across VLANs used to be a Python script I kept losing. This is a form.',
    },
    {
      persona: 'Firmware RE / Security Researcher',
      icon: IconHex,
      color: 'var(--accent-4)',
      problem: 'Dumped flash from a router — where do the config strings live? What\'s the structure?',
      flow: ['Open .bin in Hex', 'Search ASCII "config"', 'Dual-view to read text', 'Export slice'],
      tools: ['hex'],
      quote: 'It\'s xxd + grep + less in one panel, in the browser. Hard to go back.',
    },
    {
      persona: 'Protocol Implementer',
      icon: IconFlow,
      color: 'var(--accent-5)',
      problem: 'Writing a new TLS proxy — need well-formed Client Hello test cases with varying SNI.',
      flow: ['Generate TLS with SNI=A', 'Edit SNI → B,C,D', 'Download matrix'],
      tools: ['generator', 'editor'],
      quote: 'I can now build a golden test corpus in an afternoon.',
    },
    {
      persona: 'Instructor / Trainer',
      icon: IconUseCases,
      color: 'var(--accent-3)',
      problem: 'Teaching a networking course — need synthetic captures demonstrating specific protocol behaviors.',
      flow: ['Generate clean DNS/UDP', 'Edit queries to teaching examples', 'Share with class'],
      tools: ['generator', 'editor'],
      quote: 'Students can see exactly what a malformed SYN-ACK looks like without tcpdump on a live net.',
    },
    {
      persona: 'Compliance / Audit',
      icon: IconPDF,
      color: 'var(--accent-3)',
      problem: 'Editing findings in existing audit PDFs without re-exporting from Word.',
      flow: ['Open audit.pdf', 'Click text, edit', 'Save as new PDF'],
      tools: ['pdf'],
      quote: 'Minor corrections no longer mean opening Acrobat.',
    },
  ];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <ViewHeader
        icon={IconUseCases}
        title="Use cases"
        subtitle="Real workflows DevToolBox was built for. Each chains 1-3 tools together."
      />
      <div style={{ padding: '8px 28px 40px', overflow: 'auto', flex: 1 }}>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 14 }}>
          {cases.map(c => (
            <div key={c.persona} style={{
              background: 'var(--panel)',
              border: '1px solid var(--line)',
              borderLeft: `2px solid ${c.color}`,
              borderRadius: 6,
              padding: 18,
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 10 }}>
                <div style={{
                  width: 30, height: 30, borderRadius: 6,
                  background: `color-mix(in oklab, ${c.color} 12%, transparent)`,
                  color: c.color,
                  display: 'grid', placeItems: 'center',
                }}>
                  <c.icon size={15}/>
                </div>
                <div style={{ fontSize: 14, fontWeight: 600 }}>{c.persona}</div>
                <div style={{ marginLeft: 'auto', display: 'flex', gap: 4 }}>
                  {c.tools.map(t => <Tag key={t} fg="var(--text-dim)">{t}</Tag>)}
                </div>
              </div>
              <div style={{ fontSize: 12.5, color: 'var(--text-dim)', lineHeight: 1.55, marginBottom: 12 }}>
                {c.problem}
              </div>
              <div className="mono" style={{ fontSize: 11, color: 'var(--text-mute)', letterSpacing: '0.1em', marginBottom: 6 }}>
                WORKFLOW
              </div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 5, marginBottom: 12 }}>
                {c.flow.map((s, i) => (
                  <React.Fragment key={i}>
                    <span className="mono" style={{
                      fontSize: 11, padding: '3px 8px',
                      background: 'var(--panel-3)', border: '1px solid var(--line)',
                      borderRadius: 3, color: 'var(--text)',
                    }}>{s}</span>
                    {i < c.flow.length - 1 && <span style={{ color: 'var(--text-mute)' }}>→</span>}
                  </React.Fragment>
                ))}
              </div>
              <div style={{
                fontSize: 12, fontStyle: 'italic', color: c.color,
                borderLeft: `2px solid ${c.color}`, paddingLeft: 10, lineHeight: 1.45,
              }}>
                "{c.quote}"
              </div>
            </div>
          ))}
        </div>

        <div style={{ marginTop: 36 }}>
          <SectionHeading kicker="— API" title="Automation surface"
            desc="Every tool has an HTTP endpoint. Script the whole thing from CI."
          />
          <div style={{
            background: 'var(--panel)', border: '1px solid var(--line)',
            borderRadius: 6, overflow: 'hidden',
          }}>
            {[
              ['POST', '/api/upload-pcap',    'Upload PCAP/PCAPNG',           'var(--accent-2)'],
              ['GET',  '/api/pcap/:id',       'Get parsed packet list',       'var(--accent)'],
              ['PUT',  '/api/pcap/:id/:pkt',  'Rewrite packet fields',         'var(--accent-3)'],
              ['POST', '/api/generate-pcap',  'Synthesize flows',             'var(--accent-2)'],
              ['POST', '/api/merge-pcaps',    'Merge multiple captures',      'var(--accent-2)'],
              ['POST', '/api/upload-binary',  'Upload to Hex Viewer',         'var(--accent-2)'],
              ['GET',  '/api/hex/:id',        'Page of bytes',                'var(--accent)'],
              ['POST', '/api/hex/:id/search', 'Hex or ASCII search',          'var(--accent-2)'],
            ].map(([m, path, desc, c]) => (
              <div key={path} style={{
                display: 'grid', gridTemplateColumns: '70px 1fr 2fr',
                padding: '10px 16px', gap: 14,
                borderBottom: '1px solid color-mix(in oklab, var(--line) 60%, transparent)',
                fontFamily: 'var(--mono)', fontSize: 12,
              }}>
                <span style={{ color: c, fontWeight: 600 }}>{m}</span>
                <span style={{ color: 'var(--text)' }}>{path}</span>
                <span style={{ color: 'var(--text-dim)' }}>{desc}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

Object.assign(window, { UseCasesView });

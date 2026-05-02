/* PCAP Generator — protocol config, live preview */

function PCAPGeneratorView() {
  const [proto, setProto] = React.useState('tls');
  const [count, setCount] = React.useState(10);
  const [vlan, setVlan] = React.useState('2018');
  const [srcIp, setSrcIp] = React.useState('10.0.1.42');
  const [dstIp, setDstIp] = React.useState('10.0.2.17');
  const [sport, setSport] = React.useState('54211');
  const [dport, setDport] = React.useState('443');
  const [sni, setSni] = React.useState('api.internal.corp');
  const [host, setHost] = React.useState('api.example.com');
  const [dns, setDns] = React.useState('service.local');
  const [generating, setGenerating] = React.useState(false);
  const [generated, setGenerated] = React.useState(false);
  const [progress, setProgress] = React.useState(0);

  const protos = [
    { k: 'tcp', l: 'TCP', d: '3-way handshake + data + FIN', c: 'var(--accent)' },
    { k: 'http', l: 'HTTP', d: 'GET/200 over TCP', c: 'var(--accent-3)' },
    { k: 'udp', l: 'UDP', d: 'Stateless datagrams', c: 'var(--accent-2)' },
    { k: 'dns_udp', l: 'DNS/UDP', d: 'A, AAAA, MX queries', c: 'var(--accent-5)' },
    { k: 'dns_tcp', l: 'DNS/TCP', d: 'Large response scenarios', c: 'var(--accent-5)' },
    { k: 'tls', l: 'TLS', d: 'Client Hello + Server Hello', c: 'var(--accent-4)' },
    { k: 'icmp', l: 'ICMP', d: 'Echo req/reply', c: 'var(--text-dim)' },
    { k: 'arp', l: 'ARP', d: 'Who-has broadcasts', c: 'var(--text-dim)' },
  ];
  const current = protos.find(p => p.k === proto);

  const generate = () => {
    setGenerating(true);
    setGenerated(false);
    setProgress(0);
    const t = setInterval(() => {
      setProgress(p => {
        if (p >= 100) {
          clearInterval(t);
          setGenerating(false);
          setGenerated(true);
          return 100;
        }
        return p + 8;
      });
    }, 60);
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <ViewHeader
        icon={IconGenerator}
        title="PCAP Generator"
        subtitle="Synthesize realistic traffic with full protocol flows and correct checksums."
      />
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 18, padding: '8px 28px 28px', flex: 1, minHeight: 0, overflow: 'auto' }}>

        {/* LEFT: config */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          <Panel title="1. Protocol" subtitle="Each protocol determines the packet sequence and layers.">
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 6 }}>
              {protos.map(p => (
                <button key={p.k} onClick={() => setProto(p.k)} style={{
                  display: 'flex', flexDirection: 'column', alignItems: 'flex-start', gap: 3,
                  padding: '10px 12px', textAlign: 'left',
                  background: proto === p.k ? 'color-mix(in oklab, var(--accent) 10%, transparent)' : 'var(--panel-2)',
                  border: '1px solid ' + (proto === p.k ? 'color-mix(in oklab, var(--accent) 35%, transparent)' : 'var(--line)'),
                  borderRadius: 5,
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <span style={{ width: 7, height: 7, borderRadius: 7, background: p.c }}/>
                    <span className="mono" style={{ fontSize: 12.5, color: p.c, fontWeight: 600 }}>{p.l}</span>
                  </div>
                  <span style={{ fontSize: 11, color: 'var(--text-dim)' }}>{p.d}</span>
                </button>
              ))}
            </div>
          </Panel>

          <Panel title="2. Count & VLAN">
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
              <Field label="packet count" value={count} onChange={v => setCount(+v)} suffix="1-1000" type="number"/>
              <Field label="vlan id" value={vlan} onChange={setVlan} suffix="optional"/>
            </div>
          </Panel>

          <Panel title="3. Network">
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
              <Field label="src ip" value={srcIp} onChange={setSrcIp}/>
              <Field label="dst ip" value={dstIp} onChange={setDstIp} suffix="auto ++" suffixColor="var(--accent)"/>
              <Field label="src port" value={sport} onChange={setSport}/>
              <Field label="dst port" value={dport} onChange={setDport}/>
            </div>
          </Panel>

          {(proto === 'tls' || proto === 'http' || proto.startsWith('dns')) && (
            <Panel title="4. Protocol-specific">
              {proto === 'tls' && <Field label="SNI (server name)" value={sni} onChange={setSni} color="var(--accent-4)"/>}
              {proto === 'http' && <Field label="Host header" value={host} onChange={setHost} color="var(--accent-3)"/>}
              {proto.startsWith('dns') && <Field label="query name" value={dns} onChange={setDns} color="var(--accent-5)"/>}
            </Panel>
          )}

          <button onClick={generate} disabled={generating} style={{
            padding: '12px 18px', fontSize: 13.5, fontWeight: 600,
            background: generating ? 'var(--panel-3)' : 'var(--accent)',
            color: generating ? 'var(--text-dim)' : '#0b0d10',
            border: 'none', borderRadius: 6, cursor: generating ? 'wait' : 'pointer',
            display: 'inline-flex', alignItems: 'center', justifyContent: 'center', gap: 8,
          }}>
            {generating ? <><span style={{ animation: 'pulse 1s infinite' }}>●</span> Generating…</> : <><IconPlay size={13}/> Generate PCAP</>}
          </button>
        </div>

        {/* RIGHT: preview */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 14, minWidth: 0 }}>
          <Panel title="Command preview" subtitle="The equivalent scapy call" padding={0}>
            <pre className="mono" style={{
              margin: 0, padding: 14, background: 'var(--bg)', color: 'var(--text-dim)',
              fontSize: 12, lineHeight: 1.7, overflow: 'auto',
            }}>
<span style={{ color: 'var(--accent)' }}>POST</span> /api/generate-pcap<br/>
<span style={{ color: 'var(--text-mute)' }}>Content-Type:</span> application/json{'\n\n'}
{`{`}{'\n'}
{`  "protocol":      `}<span style={{ color: current.c }}>{`"${proto}"`}</span>,{'\n'}
{`  "packet_count":  `}<span style={{ color: 'var(--accent-2)' }}>{count}</span>,{'\n'}
{`  "vlan_id":       `}<span style={{ color: 'var(--accent-2)' }}>{vlan}</span>,{'\n'}
{`  "src_ip":        `}<span style={{ color: 'var(--accent-2)' }}>{`"${srcIp}"`}</span>,{'\n'}
{`  "dst_ip":        `}<span style={{ color: 'var(--accent-2)' }}>{`"${dstIp}"`}</span>,{'\n'}
{`  "src_port":      `}<span style={{ color: 'var(--accent-2)' }}>{sport}</span>,{'\n'}
{`  "dst_port":      `}<span style={{ color: 'var(--accent-2)' }}>{dport}</span>,{'\n'}
{proto === 'tls' && <>{`  "sni":           `}<span style={{ color: 'var(--accent-4)' }}>{`"${sni}"`}</span>{'\n'}</>}
{proto === 'http' && <>{`  "host":          `}<span style={{ color: 'var(--accent-3)' }}>{`"${host}"`}</span>{'\n'}</>}
{proto.startsWith('dns') && <>{`  "query":         `}<span style={{ color: 'var(--accent-5)' }}>{`"${dns}"`}</span>{'\n'}</>}
{`}`}
            </pre>
          </Panel>

          <Panel title={generated ? 'Generated' : 'Output'} subtitle={generated ? `${count * flowLength(proto)} packets ready to download` : 'Click Generate to see result'}>
            {!generating && !generated && (
              <div style={{ padding: 28, textAlign: 'center', color: 'var(--text-mute)', fontSize: 12.5 }}>
                <IconGenerator size={26} style={{ opacity: 0.4, marginBottom: 10 }}/>
                <div>No output yet. Configure and generate.</div>
              </div>
            )}
            {generating && (
              <div style={{ padding: 20 }}>
                <div style={{ fontSize: 12, color: 'var(--text-dim)', marginBottom: 8, fontFamily: 'var(--mono)' }}>
                  building {proto.toUpperCase()} flow… {progress}%
                </div>
                <div style={{ height: 6, background: 'var(--panel-3)', borderRadius: 3, overflow: 'hidden' }}>
                  <div style={{ height: '100%', width: progress + '%', background: 'var(--accent)', transition: 'width 0.1s' }}/>
                </div>
              </div>
            )}
            {generated && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                <div style={{
                  display: 'flex', alignItems: 'center', gap: 10,
                  padding: '10px 12px',
                  background: 'color-mix(in oklab, var(--accent) 8%, transparent)',
                  border: '1px solid color-mix(in oklab, var(--accent) 25%, transparent)',
                  borderRadius: 5,
                }}>
                  <IconCheck size={15} style={{ color: 'var(--accent)' }}/>
                  <span className="mono" style={{ fontSize: 12 }}>generated_{proto}_{count}pkts_20260424_1134.pcap</span>
                </div>
                <div className="mono" style={{ fontSize: 11.5, color: 'var(--text-dim)', lineHeight: 1.7 }}>
                  total packets  <span style={{ color: 'var(--text)' }}>{count * flowLength(proto)}</span><br/>
                  file size      <span style={{ color: 'var(--text)' }}>{(count * flowLength(proto) * 84).toLocaleString()} bytes</span><br/>
                  dst ip range   <span style={{ color: 'var(--accent-2)' }}>{dstIp} → {incrementIp(dstIp, count-1)}</span><br/>
                  checksums      <span style={{ color: 'var(--accent)' }}>✓ all valid</span>
                </div>
                <div style={{ display: 'flex', gap: 8 }}>
                  <button style={{ ...btnStyles.primary, flex: 1 }}>
                    <IconDownload size={13}/> Download
                  </button>
                  <button style={{ ...btnStyles.ghost, flex: 1 }}>
                    <IconEditor size={13}/> Open in Editor
                  </button>
                </div>
              </div>
            )}
          </Panel>

          <Panel title="Flow structure" subtitle={`${flowLength(proto)} packets per flow × ${count} flows`}>
            <FlowDiagram proto={proto}/>
          </Panel>
        </div>
      </div>
    </div>
  );
}

function flowLength(p) {
  return { tcp: 6, http: 8, udp: 1, dns_udp: 2, dns_tcp: 4, tls: 8, icmp: 2, arp: 1 }[p] || 1;
}
function incrementIp(ip, n) {
  const parts = ip.split('.').map(Number);
  parts[3] = (parts[3] + n) & 0xff;
  return parts.join('.');
}

function FlowDiagram({ proto }) {
  const flows = {
    tcp:  [['SYN','var(--accent)'],['SYN-ACK','var(--accent)'],['ACK','var(--text-dim)'],['PSH-ACK','var(--accent-4)'],['ACK','var(--text-dim)'],['FIN-ACK','var(--accent-3)']],
    http: [['SYN','var(--accent)'],['SYN-ACK','var(--accent)'],['ACK','var(--text-dim)'],['GET','var(--accent-3)'],['200 OK','var(--accent-3)'],['ACK','var(--text-dim)'],['FIN-ACK','var(--accent-3)'],['ACK','var(--text-dim)']],
    tls:  [['SYN','var(--accent)'],['SYN-ACK','var(--accent)'],['ACK','var(--text-dim)'],['Client Hello','var(--accent-4)'],['Server Hello','var(--accent-4)'],['Certificate','var(--accent-4)'],['Finished','var(--accent-4)'],['ACK','var(--text-dim)']],
    dns_udp: [['Query','var(--accent-5)'],['Response','var(--accent-5)']],
    dns_tcp: [['SYN','var(--accent)'],['SYN-ACK','var(--accent)'],['Query','var(--accent-5)'],['Response','var(--accent-5)']],
    udp: [['Datagram','var(--accent-2)']],
    icmp: [['Echo Request','var(--text-dim)'],['Echo Reply','var(--text-dim)']],
    arp: [['Who-Has','var(--text-dim)']],
  };
  const steps = flows[proto] || [];
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
      {steps.map(([label, color], i) => (
        <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '3px 4px' }}>
          <span className="mono" style={{ fontSize: 10.5, color: 'var(--text-mute)', width: 24 }}>{String(i+1).padStart(2,'0')}</span>
          <span style={{ width: 7, height: 7, borderRadius: 7, background: color }}/>
          <span className="mono" style={{ fontSize: 12, color }}>{label}</span>
          <span style={{ flex: 1, height: 1, background: `color-mix(in oklab, ${color} 20%, transparent)` }}/>
        </div>
      ))}
    </div>
  );
}

function Field({ label, value, onChange, type, suffix, suffixColor, color }) {
  return (
    <div>
      <div className="mono" style={{ fontSize: 10.5, color: 'var(--text-mute)', marginBottom: 4, letterSpacing: '0.1em' }}>
        {label.toUpperCase()}
        {suffix && <span style={{ marginLeft: 6, color: suffixColor || 'var(--text-mute)', textTransform: 'none', letterSpacing: 0 }}>{suffix}</span>}
      </div>
      <input
        type={type || 'text'}
        value={value}
        onChange={e => onChange(e.target.value)}
        className="mono"
        style={{
          width: '100%', padding: '8px 10px',
          background: 'var(--panel-2)', border: '1px solid var(--line)',
          borderRadius: 4, color: color || 'var(--text)',
          fontSize: 12.5, fontFamily: 'var(--mono)', outline: 'none',
          boxSizing: 'border-box',
        }}
      />
    </div>
  );
}

const btnStyles = {
  primary: {
    display: 'inline-flex', alignItems: 'center', justifyContent: 'center', gap: 6,
    padding: '8px 12px', fontSize: 12, fontWeight: 600,
    background: 'var(--accent)', color: '#0b0d10',
    border: 'none', borderRadius: 5,
  },
  ghost: {
    display: 'inline-flex', alignItems: 'center', justifyContent: 'center', gap: 6,
    padding: '8px 12px', fontSize: 12, fontWeight: 500,
    background: 'var(--panel-2)', color: 'var(--text)',
    border: '1px solid var(--line-2)', borderRadius: 5,
  },
};

Object.assign(window, { PCAPGeneratorView, Field, btnStyles });

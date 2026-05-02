export const SAMPLE_PACKETS = [
  { i: 1,  t: 0.000000, src: '10.0.1.42',   dst: '10.0.2.17',   sport: 54211, dport: 443,   proto: 'TCP',  flag: 'SYN',      len: 74,   info: 'Seq=0 Win=64240',  layers: ['ETH','IPv4','TCP'], sni: null },
  { i: 2,  t: 0.000412, src: '10.0.2.17',   dst: '10.0.1.42',   sport: 443,   dport: 54211, proto: 'TCP',  flag: 'SYN-ACK',  len: 74,   info: 'Seq=0 Ack=1 Win=65535', layers: ['ETH','IPv4','TCP'], sni: null },
  { i: 3,  t: 0.000601, src: '10.0.1.42',   dst: '10.0.2.17',   sport: 54211, dport: 443,   proto: 'TCP',  flag: 'ACK',      len: 66,   info: 'Seq=1 Ack=1 Win=64240', layers: ['ETH','IPv4','TCP'], sni: null },
  { i: 4,  t: 0.001102, src: '10.0.1.42',   dst: '10.0.2.17',   sport: 54211, dport: 443,   proto: 'TLS',  flag: 'PSH-ACK',  len: 583,  info: 'Client Hello', layers: ['ETH','IPv4','TCP','TLS'], sni: 'api.internal.corp' },
  { i: 5,  t: 0.002011, src: '10.0.2.17',   dst: '10.0.1.42',   sport: 443,   dport: 54211, proto: 'TLS',  flag: 'PSH-ACK',  len: 1422, info: 'Server Hello, Certificate', layers: ['ETH','IPv4','TCP','TLS'], sni: null },
  { i: 6,  t: 0.002517, src: '10.0.1.42',   dst: '10.0.2.17',   sport: 54211, dport: 443,   proto: 'TCP',  flag: 'ACK',      len: 66,   info: 'Seq=518 Ack=1421 Win=131072', layers: ['ETH','IPv4','TCP'], sni: null },
  { i: 7,  t: 0.003318, src: '10.0.1.42',   dst: '10.0.3.88',   sport: 42119, dport: 53,    proto: 'DNS',  flag: 'Query',    len: 82,   info: 'A api.internal.corp', layers: ['ETH','IPv4','UDP','DNS'], sni: null },
  { i: 8,  t: 0.003901, src: '10.0.3.88',   dst: '10.0.1.42',   sport: 53,    dport: 42119, proto: 'DNS',  flag: 'Response', len: 114,  info: 'A 10.0.2.17 TTL=60', layers: ['ETH','IPv4','UDP','DNS'], sni: null },
  { i: 9,  t: 0.004444, src: '10.0.1.42',   dst: '10.0.2.22',   sport: 51880, dport: 80,    proto: 'HTTP', flag: 'Request',  len: 312,  info: 'GET /v1/health HTTP/1.1', layers: ['ETH','IPv4','TCP','HTTP'], sni: null },
  { i: 10, t: 0.005011, src: '10.0.2.22',   dst: '10.0.1.42',   sport: 80,    dport: 51880, proto: 'HTTP', flag: 'Response', len: 408,  info: 'HTTP/1.1 200 OK', layers: ['ETH','IPv4','TCP','HTTP'], sni: null },
  { i: 11, t: 0.007122, src: '10.0.1.42',   dst: '10.0.2.17',   sport: 54211, dport: 443,   proto: 'TCP',  flag: 'FIN-ACK',  len: 66,   info: 'Seq=518 Ack=1421', layers: ['ETH','IPv4','TCP'], sni: null },
  { i: 12, t: 0.007545, src: '10.0.2.17',   dst: '10.0.1.42',   sport: 443,   dport: 54211, proto: 'TCP',  flag: 'FIN-ACK',  len: 66,   info: 'Seq=1421 Ack=519', layers: ['ETH','IPv4','TCP'], sni: null },
];

export const PROTO_COLOR = {
  TCP: 'var(--accent)',
  UDP: 'var(--accent-2)',
  DNS: 'var(--accent-5)',
  HTTP: 'var(--accent-3)',
  TLS: 'var(--accent-4)',
  ICMP: 'var(--text-dim)',
  ARP: 'var(--text-dim)',
};

export const FLAG_STYLE = {
  'SYN':       { bg: 'color-mix(in oklab, var(--accent) 20%, transparent)',   fg: 'var(--accent)' },
  'SYN-ACK':   { bg: 'color-mix(in oklab, var(--accent) 20%, transparent)',   fg: 'var(--accent)' },
  'ACK':       { bg: 'color-mix(in oklab, var(--text-dim) 20%, transparent)', fg: 'var(--text-dim)' },
  'PSH-ACK':   { bg: 'color-mix(in oklab, var(--accent-4) 20%, transparent)', fg: 'var(--accent-4)' },
  'FIN-ACK':   { bg: 'color-mix(in oklab, var(--accent-3) 20%, transparent)', fg: 'var(--accent-3)' },
  'Query':     { bg: 'color-mix(in oklab, var(--accent-5) 20%, transparent)', fg: 'var(--accent-5)' },
  'Response':  { bg: 'color-mix(in oklab, var(--accent-2) 20%, transparent)', fg: 'var(--accent-2)' },
  'Request':   { bg: 'color-mix(in oklab, var(--accent-3) 20%, transparent)', fg: 'var(--accent-3)' },
  'Echo':      { bg: 'color-mix(in oklab, var(--accent-2) 20%, transparent)', fg: 'var(--accent-2)' },
  'Reply':     { bg: 'color-mix(in oklab, var(--accent-2) 20%, transparent)', fg: 'var(--accent-2)' },
};

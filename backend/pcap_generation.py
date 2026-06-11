"""
PCAP generation — synthetic capture builders (mixin for PCAPHandler).

Split out of pcap_handler.py. Methods rely on PCAPHandler core helpers
(self._resolve, self.upload_folder) provided via inheritance.
"""
import os
from scapy.all import rdpcap, wrpcap, IP, IPv6, TCP, UDP, ICMP, Raw, Ether, Dot1Q, DNS, DNSQR, DNSRR, ARP


class GenerationMixin:
    """Synthetic PCAP generation, merging, and field extraction."""

    def generate_pcap(self, protocol, packet_count, vlan_id=None, options=None):
        """Generate PCAP file with specified protocol and options"""
        try:
            from datetime import datetime
            import random
            import ipaddress
            
            if options is None:
                options = {}
            
            packets = []
            
            # Default values
            src_mac = options.get('src_mac', '00:0c:29:63:c0:fb')
            dst_mac = options.get('dst_mac', '00:0c:29:63:c0:fa')
            base_src_ip = options.get('src_ip', '192.168.1.100')
            base_dst_ip = options.get('dst_ip', '192.168.1.200')
            src_port = options.get('src_port', random.randint(49152, 65535))
            dst_port = options.get('dst_port', 80)

            # Optional fixed total frame size (Ethernet header → end of payload,
            # i.e. what len(pkt) reports — no FCS). Applied to data packets only.
            target_size = options.get('packet_size')
            if target_size is not None:
                try:
                    target_size = int(target_size)
                except (TypeError, ValueError):
                    return {'success': False, 'error': 'packet_size must be an integer'}
                if target_size < 1 or target_size > 65535:
                    return {'success': False, 'error': 'packet_size must be between 1 and 65535 bytes'}
                options['packet_size'] = target_size  # normalise for the flow builder

            # Which address(es) to increment across packets/flows. Defaults
            # preserve historical behaviour: dst increments, src stays fixed.
            inc_src = bool(options.get('increment_src_ip', False))
            inc_dst = bool(options.get('increment_dst_ip', True))

            # Port increment toggles. Defaults preserve historical behaviour:
            # src port walks per flow, dst port stays fixed.
            inc_src_port = bool(options.get('increment_src_port', True))
            inc_dst_port = bool(options.get('increment_dst_port', False))

            # Effective base dst port: tcp/udp use the configured value, the
            # other protocols use their well-known port.
            if protocol == 'http':
                dst_port_base = 80
            elif protocol == 'tls':
                dst_port_base = 443
            elif protocol in ('dns_tcp', 'dns_udp'):
                dst_port_base = 53
            else:  # tcp, udp, icmp, arp (ports unused for the latter two)
                dst_port_base = dst_port

            # Parse base IPs to allow incrementing
            try:
                base_dst_ip_obj = ipaddress.ip_address(base_dst_ip)
            except ValueError:
                base_dst_ip_obj = ipaddress.ip_address('192.168.1.200')
            try:
                base_src_ip_obj = ipaddress.ip_address(base_src_ip)
            except ValueError:
                base_src_ip_obj = None

            for i in range(packet_count):
                # Per-packet/flow addresses, honouring the increment toggles
                current_dst_ip = str(base_dst_ip_obj + i) if inc_dst else str(base_dst_ip_obj)
                if inc_src and base_src_ip_obj is not None:
                    src_ip = str(base_src_ip_obj + i)
                else:
                    src_ip = base_src_ip
                # Per-flow ports, honouring the increment toggles (wrap within 1..65535)
                current_src_port = (((src_port - 1 + i) % 65535) + 1) if inc_src_port else src_port
                current_dst_port = (((dst_port_base - 1 + i) % 65535) + 1) if inc_dst_port else dst_port_base
                
                # Generate based on protocol
                if protocol == 'tcp' or protocol == 'http' or protocol == 'tls':
                    # Generate complete TCP flow for TCP-based protocols
                    flow_packets = self._generate_tcp_flow(
                        src_mac, dst_mac, src_ip, current_dst_ip,
                        current_src_port, current_dst_port,
                        protocol, vlan_id, i, options
                    )
                    packets.extend(flow_packets)
                
                elif protocol == 'udp':
                    # Build Ethernet layer
                    eth = Ether(src=src_mac, dst=dst_mac)
                    if vlan_id is not None:
                        eth = eth / Dot1Q(vlan=vlan_id)

                    # UDP doesn't need full flow - single packet
                    ip_l = self._ip_layer(src_ip, current_dst_ip)
                    udp_l = UDP(sport=current_src_port, dport=current_dst_port)
                    load = f"UDP Packet {i+1}".encode()
                    if target_size:
                        load = self._fit_payload(eth / ip_l / udp_l, load, target_size)
                    pkt = eth / ip_l / udp_l / Raw(load=load)
                    packets.append(pkt)
                
                elif protocol == 'dns_udp':
                    # Build Ethernet layer
                    eth = Ether(src=src_mac, dst=dst_mac)
                    if vlan_id is not None:
                        eth = eth / Dot1Q(vlan=vlan_id)

                    dns_query = options.get('dns_query', 'example.com')
                    dns_rr = self._build_dns_answer(dns_query, current_dst_ip, src_ip, options)
                    qtype_num = dns_rr['qtype']
                    answer_rr = dns_rr['rr']

                    ip_fwd = self._ip_layer(src_ip, current_dst_ip)
                    ip_rev = self._ip_layer(current_dst_ip, src_ip)

                    udp_q = UDP(sport=current_src_port, dport=current_dst_port)
                    if target_size:
                        overhead = len(eth / ip_fwd / udp_q)
                        dns_q = self._build_sized_dns(dns_query, qtype_num, target_size - overhead)
                    else:
                        dns_q = DNS(rd=1, qd=DNSQR(qname=dns_query, qtype=qtype_num))
                    query_pkt = eth / ip_fwd / udp_q / dns_q
                    packets.append(query_pkt)

                    if not options.get('dns_query_only'):
                        response_pkt = eth / ip_rev / UDP(sport=current_dst_port, dport=current_src_port) / DNS(
                            id=query_pkt[DNS].id, qr=1, aa=1,
                            qd=DNSQR(qname=dns_query, qtype=qtype_num),
                            an=answer_rr
                        )
                        packets.append(response_pkt)
                
                elif protocol == 'dns_tcp':
                    # Generate complete TCP flow with DNS payload
                    flow_packets = self._generate_tcp_flow(
                        src_mac, dst_mac, src_ip, current_dst_ip,
                        current_src_port, current_dst_port, protocol, vlan_id, i, options
                    )
                    packets.extend(flow_packets)

                elif protocol == 'icmp':
                    # Build Ethernet layer
                    eth = Ether(src=src_mac, dst=dst_mac)
                    eth_rev = Ether(src=dst_mac, dst=src_mac)
                    if vlan_id is not None:
                        eth = eth / Dot1Q(vlan=vlan_id)
                        eth_rev = eth_rev / Dot1Q(vlan=vlan_id)
                    icmp_id = (i + 1) & 0xFFFF
                    icmp_seq = (i + 1) & 0xFFFF
                    base_payload = options.get('icmp_payload', 'DevToolBox ICMP').encode()

                    import ipaddress as _ipaddr
                    try:
                        _is_v6 = _ipaddr.ip_address(src_ip).version == 6
                    except ValueError:
                        _is_v6 = False

                    if _is_v6:
                        from scapy.layers.inet6 import ICMPv6EchoRequest, ICMPv6EchoReply
                        req_hdr = eth / IPv6(src=src_ip, dst=current_dst_ip) / ICMPv6EchoRequest(id=icmp_id, seq=icmp_seq)
                        rep_hdr = eth_rev / IPv6(src=current_dst_ip, dst=src_ip) / ICMPv6EchoReply(id=icmp_id, seq=icmp_seq)
                    else:
                        req_hdr = eth / IP(src=src_ip, dst=current_dst_ip) / ICMP(type=8, code=0, id=icmp_id, seq=icmp_seq)
                        rep_hdr = eth_rev / IP(src=current_dst_ip, dst=src_ip) / ICMP(type=0, code=0, id=icmp_id, seq=icmp_seq)

                    payload = self._fit_payload(req_hdr, base_payload, target_size) if target_size else base_payload[:56]
                    req = req_hdr / Raw(load=payload)
                    rep = rep_hdr / Raw(load=payload)
                    packets.append(req)
                    packets.append(rep)

                elif protocol == 'arp':
                    target_ip = options.get('target_ip', current_dst_ip)
                    eth_arp_req = Ether(src=src_mac, dst='ff:ff:ff:ff:ff:ff')
                    eth_arp_rep = Ether(src=dst_mac, dst=src_mac)
                    if vlan_id is not None:
                        eth_arp_req = eth_arp_req / Dot1Q(vlan=vlan_id)
                        eth_arp_rep = eth_arp_rep / Dot1Q(vlan=vlan_id)
                    arp_req = eth_arp_req / ARP(
                        op='who-has', hwsrc=src_mac, psrc=src_ip,
                        hwdst='00:00:00:00:00:00', pdst=target_ip
                    )
                    packets.append(arp_req)
                    arp_rep = eth_arp_rep / ARP(
                        op='is-at', hwsrc=dst_mac, psrc=target_ip,
                        hwdst=src_mac, pdst=src_ip
                    )
                    packets.append(arp_rep)

                else:
                    return {'success': False, 'error': f'Unsupported protocol: {protocol}'}
            
            # Generate filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            vlan_suffix = f"_vlan{vlan_id}" if vlan_id else ""
            filename = f"generated_{protocol}{vlan_suffix}_{packet_count}pkts_{timestamp}.pcap"
            filepath = os.path.join(self.upload_folder, filename)
            
            # Write PCAP
            wrpcap(filepath, packets)
            
            return {
                'success': True,
                'filepath': filepath,  # Return full path for consistency with upload endpoint
                'packet_count': len(packets),
                'protocol': protocol,
                'vlan_id': vlan_id
            }
        
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def merge_pcaps(self, filepaths, output_name=None):
        """Merge multiple PCAP/PCAPNG files into a single PCAP"""
        try:
            from datetime import datetime

            if not filepaths or len(filepaths) < 2:
                return {'success': False, 'error': 'At least two PCAP files are required for merge'}

            merged_packets = []
            source_files = []
            allowed_ext = {'pcap', 'pcapng'}

            for fp in filepaths:
                # Resolve + contain within the upload folder
                try:
                    resolved_path = self._resolve(fp)
                except (ValueError, FileNotFoundError) as e:
                    return {'success': False, 'error': str(e)}

                ext = os.path.splitext(resolved_path)[1].lower().lstrip('.')
                if ext not in allowed_ext:
                    return {'success': False, 'error': f'Unsupported file type: {resolved_path}'}

                packets = rdpcap(resolved_path)
                merged_packets.extend(packets)
                source_files.append(os.path.basename(resolved_path))

            if output_name:
                safe_name = os.path.basename(output_name)
            else:
                safe_name = f"merged_{len(filepaths)}files_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pcap"

            if not safe_name.lower().endswith(('.pcap', '.pcapng')):
                safe_name += '.pcap'

            output_path = os.path.join(self.upload_folder, safe_name)
            wrpcap(output_path, merged_packets)

            return {
                'success': True,
                'filepath': output_path,
                'packet_count': len(merged_packets),
                'source_files': source_files
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def extract_field_values(self, filepath):
        """
        Read a PCAP/PCAPNG file and return sorted unique values
        for each configurable generator field.
        """
        try:
            packets = rdpcap(self._resolve(filepath))

            src_macs, dst_macs = set(), set()
            src_ips,  dst_ips  = set(), set()
            src_ports, dst_ports = set(), set()
            vlans = set()

            for pkt in packets:
                if pkt.haslayer(Ether):
                    src_macs.add(pkt[Ether].src)
                    dst_macs.add(pkt[Ether].dst)
                if pkt.haslayer(Dot1Q):
                    vlans.add(pkt[Dot1Q].vlan)
                if pkt.haslayer(IP):
                    src_ips.add(pkt[IP].src)
                    dst_ips.add(pkt[IP].dst)
                if pkt.haslayer(IPv6):
                    src_ips.add(pkt[IPv6].src)
                    dst_ips.add(pkt[IPv6].dst)
                if pkt.haslayer(TCP):
                    src_ports.add(pkt[TCP].sport)
                    dst_ports.add(pkt[TCP].dport)
                if pkt.haslayer(UDP):
                    src_ports.add(pkt[UDP].sport)
                    dst_ports.add(pkt[UDP].dport)

            return {
                'success': True,
                'packet_count': len(packets),
                'fields': {
                    'src_mac':  sorted(src_macs),
                    'dst_mac':  sorted(dst_macs),
                    'src_ip':   sorted(src_ips),
                    'dst_ip':   sorted(dst_ips),
                    'src_port': sorted(src_ports),
                    'dst_port': sorted(dst_ports),
                    'vlan_id':  sorted(vlans),
                }
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _fit_payload(self, header_pkt, base_payload, target_size, fill=b'\x00'):
        """
        Return payload bytes so the full frame (header_pkt / Raw(payload)) is
        exactly target_size bytes on the wire.

        `header_pkt` is the fully-built packet WITHOUT the Raw layer, so its
        len() is the header overhead (Ethernet [+VLAN] + IP + L4). The base
        payload is padded with `fill` bytes or truncated to fit. If target_size
        is smaller than the header overhead, an empty payload is returned (the
        frame will then be header-sized, which is the smallest possible).
        """
        overhead = len(header_pkt)
        want = target_size - overhead
        if want <= 0:
            return b''
        if len(base_payload) >= want:
            return base_payload[:want]
        return base_payload + fill * (want - len(base_payload))

    def _build_sized_dns(self, qname, qtype, target_msg_len):
        """
        Build a DNS query whose serialized length is exactly target_msg_len bytes.

        DNS uses strict framing (and length-prefixing over TCP), so a packet
        cannot be grown by appending raw bytes — trailing bytes get parsed as a
        new (malformed) message. Instead we grow the message with a valid EDNS0
        Padding option (RFC 7830, optcode 12), which dissects cleanly. If the
        target is smaller than the smallest paddable message, the plain query is
        returned (the frame then slightly differs from the requested size).
        """
        from scapy.layers.dns import DNSRROPT, EDNS0TLV

        plain = DNS(rd=1, qd=DNSQR(qname=qname, qtype=qtype))

        # Smallest message carrying an EDNS0 padding option (empty padding).
        def with_pad(n):
            return DNS(rd=1, qd=DNSQR(qname=qname, qtype=qtype),
                       ar=DNSRROPT(rclass=4096, rdata=[EDNS0TLV(optcode=12, optdata=b'\x00' * n)]))

        empty_opt_len = len(bytes(with_pad(0)))
        if target_msg_len < empty_opt_len:
            return plain

        return with_pad(target_msg_len - empty_opt_len)

    def _ip_layer(self, src, dst):
        """Return IPv6() or IP() based on whether src is an IPv6 address."""
        import ipaddress
        try:
            addr = ipaddress.ip_address(src)
            if addr.version == 6:
                return IPv6(src=src, dst=dst)
        except ValueError:
            pass
        return IP(src=src, dst=dst)

    def _build_dns_answer(self, dns_query, answer_ip, src_ip, options):
        """
        Build a DNSRR answer and matching qtype for a DNS response.

        Record type priority:
          1. Explicit dns_record_type option ('A', 'AAAA', 'CNAME', 'MX')
          2. Auto-detect from src_ip address family (IPv6 → AAAA, IPv4 → A)

        Returns {'qtype': int, 'rr': DNSRR}

        Note: Scapy 2.5.0 uses type-specific field decoders for DNSRR.rdata.
        For A (type=1) IPField and AAAA (type=28) IP6Field both expect plain
        address strings — never pre-packed bytes.
        """
        import ipaddress as _ipa

        rtype = options.get('dns_record_type', '').upper()

        # Auto-detect if not explicitly set
        if not rtype:
            try:
                rtype = 'AAAA' if _ipa.ip_address(src_ip).version == 6 else 'A'
            except ValueError:
                rtype = 'A'

        qtype_map = {'A': 1, 'AAAA': 28, 'CNAME': 5, 'MX': 15}
        qtype_num = qtype_map.get(rtype, 1)

        if rtype == 'AAAA':
            # Validate; fall back to a well-formed IPv6 address on bad input
            try:
                _ipa.IPv6Address(answer_ip)
                rdata_ip = answer_ip
            except ValueError:
                rdata_ip = '::1'
            rr = DNSRR(rrname=dns_query, type=28, ttl=300, rdata=rdata_ip)

        elif rtype == 'CNAME':
            alias = options.get('dns_cname', f'www.{dns_query}')
            rr = DNSRR(rrname=dns_query, type=5, ttl=300, rdata=alias)

        elif rtype == 'MX':
            exchange = options.get('dns_mx_exchange', f'mail.{dns_query}')
            preference = int(options.get('dns_mx_preference', 10))
            # Scapy 2.5 MX rdata: "preference exchange" as a string or DNSRRMX
            try:
                from scapy.layers.dns import DNSRRMX
                rr = DNSRRMX(rrname=dns_query, ttl=300,
                              preference=preference, exchange=exchange)
            except ImportError:
                # Older Scapy fallback — raw bytes
                import struct
                pref_bytes = struct.pack('>H', preference)
                enc = b''
                for label in exchange.rstrip('.').split('.'):
                    lb = label.encode()
                    enc += bytes([len(lb)]) + lb
                enc += b'\x00'
                rr = DNSRR(rrname=dns_query, type=15, ttl=300, rdata=pref_bytes + enc)

        else:  # A (default)
            # Validate; fall back to a well-formed IPv4 address on bad input
            try:
                _ipa.IPv4Address(answer_ip)
                rdata_ip = answer_ip
            except ValueError:
                rdata_ip = '127.0.0.1'
            rr = DNSRR(rrname=dns_query, type=1, ttl=300, rdata=rdata_ip)

        return {'qtype': qtype_num, 'rr': rr}

    def _generate_tcp_flow(self, src_mac, dst_mac, src_ip, dst_ip, src_port, dst_port, protocol, vlan_id, index, options):
        """Generate a complete TCP 3-way handshake, data exchange, and connection termination"""
        import random

        flow_packets = []

        # Optional fixed total frame size for the data-bearing packet(s).
        # Padding is appended after any protocol payload, so the segment length
        # feeds the seq/ack accounting below correctly.
        target_size = options.get('packet_size')

        # Initial sequence numbers
        client_seq = random.randint(1000, 100000)
        server_seq = random.randint(1000, 100000)

        # Build base Ethernet layer
        def build_eth():
            eth = Ether(src=src_mac, dst=dst_mac)
            if vlan_id is not None:
                eth = eth / Dot1Q(vlan=vlan_id)
            return eth

        # IP layer helper — honours IPv4 / IPv6
        def ip_fwd():
            return self._ip_layer(src_ip, dst_ip)

        def ip_rev():
            return self._ip_layer(dst_ip, src_ip)

        # 1. SYN: Client initiates connection
        syn_pkt = build_eth() / ip_fwd() / TCP(sport=src_port, dport=dst_port, flags='S', seq=client_seq)
        flow_packets.append(syn_pkt)

        # 2. SYN-ACK: Server acknowledges and sends its SYN
        synack_pkt = build_eth() / ip_rev() / TCP(sport=dst_port, dport=src_port, flags='SA', seq=server_seq, ack=client_seq + 1)
        flow_packets.append(synack_pkt)

        # 3. ACK: Client acknowledges server's SYN
        ack_pkt = build_eth() / ip_fwd() / TCP(sport=src_port, dport=dst_port, flags='A', seq=client_seq + 1, ack=server_seq + 1)
        flow_packets.append(ack_pkt)
        
        # 4. Data transfer: PSH-ACK with payload
        if protocol == 'http':
            http_request = (
                f"GET /index.html HTTP/1.1\r\n"
                f"Host: {options.get('http_host', 'example.com')}\r\n"
                f"User-Agent: PCAP-Generator/1.0\r\n"
                f"Accept: */*\r\n"
                f"\r\n"
            )
            payload = http_request.encode()
            if target_size:
                payload = self._fit_payload(
                    build_eth() / ip_fwd() / TCP(sport=src_port, dport=dst_port, flags='PA', seq=client_seq + 1, ack=server_seq + 1),
                    payload, target_size)
            data_pkt = build_eth() / ip_fwd() / TCP(sport=src_port, dport=dst_port, flags='PA', seq=client_seq + 1, ack=server_seq + 1) / Raw(load=payload)
            flow_packets.append(data_pkt)

            # HTTP Response
            http_response = (
                f"HTTP/1.1 200 OK\r\n"
                f"Content-Type: text/html\r\n"
                f"Content-Length: 13\r\n"
                f"\r\n"
                f"Hello World!\n"
            )
            response_payload = http_response.encode()
            response_pkt = build_eth() / ip_rev() / TCP(sport=dst_port, dport=src_port, flags='PA', seq=server_seq + 1, ack=client_seq + 1 + len(payload)) / Raw(load=response_payload)
            flow_packets.append(response_pkt)

            # Client ACK for response
            ack_response = build_eth() / ip_fwd() / TCP(sport=src_port, dport=dst_port, flags='A', seq=client_seq + 1 + len(payload), ack=server_seq + 1 + len(response_payload))
            flow_packets.append(ack_response)

            client_seq += len(payload)
            server_seq += len(response_payload)
            
        elif protocol == 'tls':
            # TLS Client Hello
            sni = options.get('tls_sni', 'example.com')
            tls_hello = self._build_tls_client_hello(sni)
            if target_size:
                tls_hello = self._fit_payload(
                    build_eth() / ip_fwd() / TCP(sport=src_port, dport=dst_port, flags='PA', seq=client_seq + 1, ack=server_seq + 1),
                    tls_hello, target_size)
            tls_pkt = build_eth() / ip_fwd() / TCP(sport=src_port, dport=dst_port, flags='PA', seq=client_seq + 1, ack=server_seq + 1) / Raw(load=tls_hello)
            flow_packets.append(tls_pkt)

            # TLS Server Hello (simplified)
            server_hello = b'\x16\x03\x03\x00\x31' + bytes([0x00] * 49)
            tls_response = build_eth() / ip_rev() / TCP(sport=dst_port, dport=src_port, flags='PA', seq=server_seq + 1, ack=client_seq + 1 + len(tls_hello)) / Raw(load=server_hello)
            flow_packets.append(tls_response)

            client_seq += len(tls_hello)
            server_seq += len(server_hello)

            # Client ACK for Server Hello
            tls_ack = build_eth() / ip_fwd() / TCP(sport=src_port, dport=dst_port, flags='A', seq=client_seq + 1, ack=server_seq + 1)
            flow_packets.append(tls_ack)
            
        elif protocol == 'dns_tcp':
            dns_query = options.get('dns_query', 'example.com')
            dns_rr = self._build_dns_answer(dns_query, dst_ip, src_ip, options)
            qtype_num = dns_rr['qtype']
            answer_rr = dns_rr['rr']

            if target_size:
                overhead = len(build_eth() / ip_fwd() / TCP(sport=src_port, dport=dst_port, flags='PA', seq=client_seq + 1, ack=server_seq + 1))
                # reserve 2 bytes for the DNS-over-TCP length prefix
                dns = self._build_sized_dns(dns_query, qtype_num, target_size - overhead - 2)
            else:
                dns = DNS(rd=1, qd=DNSQR(qname=dns_query, qtype=qtype_num))
            dns_bytes = bytes(dns)
            dns_len = len(dns_bytes).to_bytes(2, 'big')
            payload = dns_len + dns_bytes

            data_pkt = build_eth() / ip_fwd() / TCP(sport=src_port, dport=dst_port, flags='PA', seq=client_seq + 1, ack=server_seq + 1) / Raw(load=payload)
            flow_packets.append(data_pkt)

            if not options.get('dns_query_only'):
                dns_response = DNS(
                    id=dns.id, qr=1, aa=1,
                    qd=DNSQR(qname=dns_query, qtype=qtype_num),
                    an=answer_rr
                )
                dns_response_bytes = bytes(dns_response)
                dns_response_len = len(dns_response_bytes).to_bytes(2, 'big')
                response_payload = dns_response_len + dns_response_bytes

                response_pkt = build_eth() / ip_rev() / TCP(sport=dst_port, dport=src_port, flags='PA', seq=server_seq + 1, ack=client_seq + 1 + len(payload)) / Raw(load=response_payload)
                flow_packets.append(response_pkt)
                server_seq += len(response_payload)

            client_seq += len(payload)

        else:  # tcp
            payload = f"TCP Data Packet {index + 1}".encode()
            if target_size:
                payload = self._fit_payload(
                    build_eth() / ip_fwd() / TCP(sport=src_port, dport=dst_port, flags='PA', seq=client_seq + 1, ack=server_seq + 1),
                    payload, target_size)
            data_pkt = build_eth() / ip_fwd() / TCP(sport=src_port, dport=dst_port, flags='PA', seq=client_seq + 1, ack=server_seq + 1) / Raw(load=payload)
            flow_packets.append(data_pkt)

            # Server ACK
            ack_data = build_eth() / ip_rev() / TCP(sport=dst_port, dport=src_port, flags='A', seq=server_seq + 1, ack=client_seq + 1 + len(payload))
            flow_packets.append(ack_data)

            client_seq += len(payload)

        # 5. FIN: Client initiates connection close
        fin_pkt = build_eth() / ip_fwd() / TCP(sport=src_port, dport=dst_port, flags='FA', seq=client_seq + 1, ack=server_seq + 1)
        flow_packets.append(fin_pkt)

        # 6. ACK: Server acknowledges FIN
        ack_fin_pkt = build_eth() / ip_rev() / TCP(sport=dst_port, dport=src_port, flags='A', seq=server_seq + 1, ack=client_seq + 2)
        flow_packets.append(ack_fin_pkt)

        # 7. FIN: Server sends its FIN
        fin_server_pkt = build_eth() / ip_rev() / TCP(sport=dst_port, dport=src_port, flags='FA', seq=server_seq + 1, ack=client_seq + 2)
        flow_packets.append(fin_server_pkt)

        # 8. ACK: Client acknowledges server's FIN
        final_ack_pkt = build_eth() / ip_fwd() / TCP(sport=src_port, dport=dst_port, flags='A', seq=client_seq + 2, ack=server_seq + 2)
        flow_packets.append(final_ack_pkt)

        # Optionally drop control packets (handshake / bare ACKs / teardown),
        # keeping only the data-bearing packets. Sequence numbers were computed
        # against the full flow, so the survivors stay internally consistent.
        if options.get('payload_only'):
            flow_packets = [p for p in flow_packets if p.haslayer(Raw)]

        return flow_packets
    
    def _build_tls_client_hello(self, sni):
        """Build a TLS Client Hello packet with SNI extension"""
        import struct
        
        # TLS version 1.2
        tls_version = b'\x03\x03'
        
        # Random (32 bytes)
        random_bytes = bytes([0x00] * 32)
        
        # Session ID (empty)
        session_id = b'\x00'
        
        # Cipher Suites (2 suites)
        cipher_suites = b'\x00\x04\xc0\x2f\xc0\x30'
        
        # Compression Methods (none)
        compression = b'\x01\x00'
        
        # Build SNI extension
        sni_bytes = sni.encode('utf-8')
        sni_extension = struct.pack('>H', 0x0000)  # Extension type: SNI
        sni_list_len = len(sni_bytes) + 3
        sni_extension += struct.pack('>H', sni_list_len + 2)  # Extension length
        sni_extension += struct.pack('>H', sni_list_len)  # SNI list length
        sni_extension += b'\x00'  # Host name type
        sni_extension += struct.pack('>H', len(sni_bytes))  # Host name length
        sni_extension += sni_bytes
        
        # Extensions length
        extensions = struct.pack('>H', len(sni_extension)) + sni_extension
        
        # Build handshake message
        handshake_data = (
            tls_version + random_bytes + session_id + 
            cipher_suites + compression + extensions
        )
        
        # Handshake header
        handshake = b'\x01'  # Handshake type: Client Hello
        handshake += struct.pack('>I', len(handshake_data))[1:]  # Length (3 bytes)
        handshake += handshake_data
        
        # TLS record header
        tls_record = b'\x16'  # Content type: Handshake
        tls_record += tls_version
        tls_record += struct.pack('>H', len(handshake))
        tls_record += handshake
        
        return tls_record


"""
PCAP file handler
Manages reading, writing, and modifying PCAP files using Scapy
"""

import os
import shutil
import logging
from scapy.all import rdpcap, wrpcap, IP, IPv6, TCP, UDP, ICMP, Raw, Ether, Dot1Q, DNS, DNSQR, DNSRR, ARP
from collections import defaultdict
import binascii
import re

from utils import resolve_upload_path

logger = logging.getLogger(__name__)


class PCAPHandler:
    """Handler for PCAP file operations"""

    def __init__(self, upload_folder='uploads'):
        """Initialize PCAP handler with upload folder"""
        self.upload_folder = upload_folder
        # mtime-keyed parse cache: {abs_path: (mtime, PacketList)}.
        # Read-only callers share the cached PacketList; mutators read via
        # rdpcap() directly so they never alias (and corrupt) a cached object.
        self._cache = {}

    def _resolve(self, filepath):
        """Resolve a user-supplied path to a safe absolute path inside the
        upload folder. Raises ValueError on traversal, FileNotFoundError if
        the file does not exist."""
        return resolve_upload_path(filepath, self.upload_folder, must_exist=True)

    def _read(self, filepath):
        """Resolve + parse a PCAP, caching the result by file mtime.

        Single choke point for read-only access: path containment and caching
        both live here. A write changes the file's mtime, so the cache
        self-invalidates on the next read. Callers MUST NOT mutate the returned
        PacketList — it is shared; mutating paths call rdpcap(self._resolve(...))
        directly.
        """
        path = self._resolve(filepath)
        mtime = os.path.getmtime(path)
        cached = self._cache.get(path)
        if cached is not None and cached[0] == mtime:
            return cached[1]
        packets = rdpcap(path)
        self._cache[path] = (mtime, packets)
        return packets

    def _get_modified_filepath(self, filepath):
        """Get the path for modified file, creating it if necessary"""
        filepath = self._resolve(filepath)
        directory = os.path.dirname(filepath)
        filename = os.path.basename(filepath)
        
        # Check if this is already a modified file
        if filename.startswith('modified_'):
            return filepath
        
        # Create modified filename
        modified_filename = f'modified_{filename}'
        modified_filepath = os.path.join(directory, modified_filename)
        
        # If modified file doesn't exist, copy the original
        if not os.path.exists(modified_filepath):
            shutil.copy2(filepath, modified_filepath)
        
        return modified_filepath

    def read_pcap(self, filepath):
        """
        Read PCAP file and return list of packets with details
        """
        try:
            packets = self._read(filepath)
            packet_list = []

            for idx, pkt in enumerate(packets):
                packet_info = self._extract_packet_info(pkt, idx)
                packet_list.append(packet_info)

            return packet_list

        except Exception as e:
            raise Exception(f'Failed to read PCAP file: {str(e)}')

    def get_packet_details(self, filepath, packet_index):
        """Get detailed information about a specific packet"""
        try:
            packets = self._read(filepath)
            
            if packet_index < 0 or packet_index >= len(packets):
                return None

            pkt = packets[packet_index]
            return self._extract_packet_info(pkt, packet_index, detailed=True)

        except Exception as e:
            raise Exception(f'Failed to get packet details: {str(e)}')

    def modify_packet_payload(self, filepath, packet_index, new_payload_hex, offset=0):
        """
        Modify packet payload
        new_payload_hex: hex-encoded payload
        offset: byte offset to start modification
        """
        try:
            # Mutating path: read fresh (not via the shared read cache)
            packets = rdpcap(self._resolve(filepath))
            
            if packet_index < 0 or packet_index >= len(packets):
                return False

            pkt = packets[packet_index]
            
            # Convert hex payload to bytes
            try:
                new_payload = bytes.fromhex(new_payload_hex)
            except ValueError:
                raise Exception('Invalid hex payload format')

            # Modify the payload
            if offset == 0:
                # Replace entire payload
                if pkt.haslayer('Raw'):
                    pkt['Raw'].load = new_payload
                else:
                    from scapy.packet import Raw
                    pkt.add_payload(Raw(load=new_payload))
            else:
                # Modify at specific offset
                if pkt.haslayer('Raw'):
                    old_payload = bytes(pkt['Raw'].load)
                    modified = old_payload[:offset] + new_payload + old_payload[offset + len(new_payload):]
                    pkt['Raw'].load = modified
                else:
                    raise Exception('Packet has no payload to modify')

            # Recalculate checksums
            pkt = self._recalculate_checksums(pkt)
            packets[packet_index] = pkt

            # Write back to the (resolved) source file
            wrpcap(self._resolve(filepath), packets)
            return True

        except Exception as e:
            raise Exception(f'Failed to modify packet: {str(e)}')

    def create_pcap(self, packet_data, filepath):
        """Create a new PCAP file from packet data"""
        try:
            packets = []
            
            for pkt_data in packet_data:
                # Reconstruct packet from data
                pkt = self._reconstruct_packet(pkt_data)
                if pkt:
                    packets.append(pkt)

            if packets:
                wrpcap(filepath, packets)
                return True
            
            return False

        except Exception as e:
            raise Exception(f'Failed to create PCAP: {str(e)}')

    def get_statistics(self, filepath):
        """Get statistics about the PCAP file"""
        try:
            packets = self._read(filepath)
            
            stats = {
                'total_packets': len(packets),
                'protocols': defaultdict(int),
                'src_ips': defaultdict(int),
                'dst_ips': defaultdict(int),
                'src_ports': defaultdict(int),
                'dst_ports': defaultdict(int),
                'total_bytes': 0,
            }

            for pkt in packets:
                stats['total_bytes'] += len(pkt)

                # IP layer
                if pkt.haslayer(IP):
                    stats['protocols']['IPv4'] += 1
                    src_ip = pkt[IP].src
                    dst_ip = pkt[IP].dst
                    stats['src_ips'][src_ip] += 1
                    stats['dst_ips'][dst_ip] += 1
                elif pkt.haslayer(IPv6):
                    stats['protocols']['IPv6'] += 1

                # Transport + application layer — detect specific protocols first
                if pkt.haslayer(DNS):
                    stats['protocols']['DNS'] += 1
                    if pkt.haslayer(UDP):
                        stats['src_ports'][pkt[UDP].sport] += 1
                        stats['dst_ports'][pkt[UDP].dport] += 1
                    elif pkt.haslayer(TCP):
                        stats['src_ports'][pkt[TCP].sport] += 1
                        stats['dst_ports'][pkt[TCP].dport] += 1
                elif pkt.haslayer(TCP):
                    raw = bytes(pkt[Raw].load) if pkt.haslayer(Raw) else b''
                    if len(raw) >= 3 and raw[0] == 0x16 and raw[1] == 0x03:
                        stats['protocols']['TLS'] += 1
                    elif raw[:4] in (b'GET ', b'POST', b'HTTP', b'HEAD', b'PUT ', b'DELE'):
                        stats['protocols']['HTTP'] += 1
                    else:
                        stats['protocols']['TCP'] += 1
                    stats['src_ports'][pkt[TCP].sport] += 1
                    stats['dst_ports'][pkt[TCP].dport] += 1
                elif pkt.haslayer(UDP):
                    stats['protocols']['UDP'] += 1
                    stats['src_ports'][pkt[UDP].sport] += 1
                    stats['dst_ports'][pkt[UDP].dport] += 1

                if pkt.haslayer(ICMP):
                    stats['protocols']['ICMP'] += 1

            # Convert defaultdict to regular dict
            stats['protocols'] = dict(stats['protocols'])
            stats['src_ips'] = dict(stats['src_ips'])
            stats['dst_ips'] = dict(stats['dst_ips'])
            stats['src_ports'] = dict(stats['src_ports'])
            stats['dst_ports'] = dict(stats['dst_ports'])

            return stats

        except Exception as e:
            raise Exception(f'Failed to get statistics: {str(e)}')

    def _extract_packet_info(self, pkt, index, detailed=False):
        """Extract packet information"""
        info = {
            'index': index,
            'timestamp': float(pkt.time) if hasattr(pkt, 'time') else 0,
            'length': len(pkt),
            'layers': str(pkt.summary()),
        }

        # Derive a human-friendly packet type (e.g., SYN, SYN-ACK, PSH-ACK, UDP)
        packet_type = self._get_packet_type(pkt)
        if packet_type:
            info['packet_type'] = packet_type

        # IP Layer
        if pkt.haslayer(IP):
            info['src_ip'] = pkt[IP].src
            info['dst_ip'] = pkt[IP].dst
            info['protocol'] = pkt[IP].proto

        # IPv6 Layer
        elif pkt.haslayer(IPv6):
            info['src_ip'] = pkt[IPv6].src
            info['dst_ip'] = pkt[IPv6].dst

        # TCP Layer
        if pkt.haslayer(TCP):
            info['src_port'] = pkt[TCP].sport
            info['dst_port'] = pkt[TCP].dport
            info['flags'] = str(pkt[TCP].flags)

        # UDP Layer
        elif pkt.haslayer(UDP):
            info['src_port'] = pkt[UDP].sport
            info['dst_port'] = pkt[UDP].dport

        # Payload
        if detailed and pkt.haslayer('Raw'):
            payload = bytes(pkt['Raw'].load)
            info['payload'] = payload.hex()
            info['payload_size'] = len(payload)

        return info

    def _get_packet_type(self, pkt):
        """Determine packet type from protocol/flags for display only"""
        try:
            if pkt.haslayer(TCP):
                # Check for TLS before generic TCP flag labels
                if pkt.haslayer(Raw):
                    raw = bytes(pkt[Raw].load)
                    if len(raw) >= 3 and raw[0] == 0x16 and raw[1] == 0x03:
                        return 'TLS'
                    if raw[:4] in (b'GET ', b'POST', b'HTTP', b'HEAD', b'PUT ', b'DELE'):
                        return 'HTTP'

                # Check for DNS over TCP
                if pkt.haslayer(DNS):
                    return 'DNS'

                flags = pkt[TCP].flags
                syn = flags & 0x02
                ack = flags & 0x10
                fin = flags & 0x01
                rst = flags & 0x04
                psh = flags & 0x08

                if rst:
                    return 'RST'
                if syn and ack:
                    return 'SYN-ACK'
                if syn:
                    return 'SYN'
                if fin and ack:
                    return 'FIN-ACK'
                if fin:
                    return 'FIN'
                if psh and ack:
                    return 'PSH-ACK'
                if ack:
                    return 'ACK'
                return 'TCP'

            if pkt.haslayer(UDP):
                if pkt.haslayer(DNS):
                    return 'DNS'
                return 'UDP'
            if pkt.haslayer(ICMP):
                return 'ICMP'
            return None
        except Exception:
            return None

    def _recalculate_checksums(self, pkt):
        """Recalculate checksums for modified packets"""
        try:
            # Clear IP length and checksum - let Scapy recalculate
            if pkt.haslayer(IP):
                del pkt[IP].len
                del pkt[IP].chksum
            if pkt.haslayer(IPv6):
                del pkt[IPv6].plen
            if pkt.haslayer(TCP):
                del pkt[TCP].chksum
            if pkt.haslayer(UDP):
                del pkt[UDP].len
                del pkt[UDP].chksum
            
            # Recalculate by reconstructing
            pkt = pkt.__class__(bytes(pkt))
            return pkt
        except Exception as e:
            logger.warning('Checksum recalculation failed; returning packet with stale checksums: %s', e)
            return pkt

    def _reconstruct_packet(self, pkt_data):
        """Reconstruct packet from data dictionary"""
        try:
            # This is a simplified version - can be expanded based on data format
            return None
        except Exception:
            return None

    def get_http_host(self, filepath, packet_index):
        """Extract HTTP HOST header from packet"""
        try:
            packets = self._read(filepath)
            
            if packet_index < 0 or packet_index >= len(packets):
                return None

            pkt = packets[packet_index]
            
            # Check if it's HTTP traffic (typically port 80 or has HTTP content)
            if not pkt.haslayer(TCP) or not pkt.haslayer(Raw):
                return None
            
            payload = bytes(pkt[Raw].load)
            payload_str = payload.decode('utf-8', errors='ignore')
            
            # Look for HTTP request with Host header
            if 'HTTP/' in payload_str:
                # Extract Host header using regex
                host_match = re.search(r'Host:\s*([^\r\n]+)', payload_str, re.IGNORECASE)
                if host_match:
                    return host_match.group(1).strip()
            
            return None

        except Exception as e:
            return None

    def modify_http_host(self, filepath, packet_index, new_host):
        """Modify HTTP HOST header in packet"""
        try:
            # Use modified file to preserve original
            modified_filepath = self._get_modified_filepath(filepath)
            packets = rdpcap(modified_filepath)
            
            if packet_index < 0 or packet_index >= len(packets):
                return {'success': False, 'error': 'Invalid packet index'}

            pkt = packets[packet_index]
            
            if not pkt.haslayer(TCP) or not pkt.haslayer(Raw):
                return {'success': False, 'error': 'Not an HTTP packet'}
            
            payload = bytes(pkt[Raw].load)
            payload_str = payload.decode('utf-8', errors='ignore')
            
            # Check if it has Host header
            if 'Host:' not in payload_str:
                return {'success': False, 'error': 'No Host header found'}
            
            # Replace Host header
            new_payload_str = re.sub(
                r'Host:\s*[^\r\n]+',
                f'Host: {new_host}',
                payload_str,
                flags=re.IGNORECASE
            )
            
            # Update packet
            pkt[Raw].load = new_payload_str.encode('utf-8')
            
            # Recalculate checksums and lengths
            pkt = self._recalculate_checksums(pkt)
            
            # Convert PacketList to list, update, and write back
            packet_list = list(packets)
            packet_list[packet_index] = pkt
            
            # Write back to file
            wrpcap(modified_filepath, packet_list)
            return {'success': True, 'new_host': new_host, 'modified_filepath': modified_filepath}

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def get_tls_sni(self, filepath, packet_index):
        """Extract TLS SNI (Server Name Indication) from Client Hello"""
        try:
            packets = self._read(filepath)
            
            if packet_index < 0 or packet_index >= len(packets):
                return None

            pkt = packets[packet_index]
            
            if not pkt.haslayer(TCP) or not pkt.haslayer(Raw):
                return None
            
            payload = bytes(pkt[Raw].load)
            
            # Check for TLS Client Hello (0x16 = Handshake, 0x01 = Client Hello)
            if len(payload) < 43:
                return None
            
            # TLS record layer: type (1) + version (2) + length (2)
            if payload[0] != 0x16:  # Not a handshake
                return None
            
            # Parse TLS handshake
            # Skip to handshake protocol
            pos = 5  # After TLS record header
            
            if pos >= len(payload) or payload[pos] != 0x01:  # Not Client Hello
                return None
            
            # Extract SNI from extensions
            sni = self._extract_sni_from_payload(payload)
            return sni

        except Exception as e:
            return None

    def _extract_sni_from_payload(self, payload):
        """Helper method to extract SNI from TLS payload"""
        try:
            pos = 5  # Start after TLS record header
            
            # Skip handshake type (1) + length (3)
            pos += 4
            
            # Skip version (2) + random (32)
            pos += 34
            
            if pos >= len(payload):
                return None
            
            # Session ID length
            session_id_len = payload[pos]
            pos += 1 + session_id_len
            
            if pos + 2 >= len(payload):
                return None
            
            # Cipher suites length
            cipher_len = int.from_bytes(payload[pos:pos+2], 'big')
            pos += 2 + cipher_len
            
            if pos + 1 >= len(payload):
                return None
            
            # Compression methods length
            comp_len = payload[pos]
            pos += 1 + comp_len
            
            if pos + 2 >= len(payload):
                return None
            
            # Extensions length (clamp to the actual payload so a malformed
            # length can't drive an out-of-bounds read)
            ext_len = int.from_bytes(payload[pos:pos+2], 'big')
            pos += 2

            # Parse extensions to find SNI. Use <= so an extension whose 4-byte
            # header ends exactly at ext_end is still examined.
            ext_end = min(pos + ext_len, len(payload))
            while pos + 4 <= ext_end:
                ext_type = int.from_bytes(payload[pos:pos+2], 'big')
                ext_data_len = int.from_bytes(payload[pos+2:pos+4], 'big')
                pos += 4
                
                # SNI extension type is 0x0000
                if ext_type == 0x0000:
                    # SNI extension found
                    if pos + 5 <= len(payload):
                        # Skip list length (2) + type (1) + name length (2)
                        sni_len = int.from_bytes(payload[pos+3:pos+5], 'big')
                        sni_start = pos + 5
                        if sni_start + sni_len <= len(payload):
                            sni = payload[sni_start:sni_start+sni_len].decode('utf-8', errors='ignore')
                            return sni
                
                pos += ext_data_len
            
            return None

        except Exception:
            return None

    def modify_tls_sni(self, filepath, packet_index, new_sni):
        """Modify TLS SNI (Server Name Indication) in Client Hello"""
        try:
            # Use modified file to preserve original
            modified_filepath = self._get_modified_filepath(filepath)
            packets = rdpcap(modified_filepath)
            
            if packet_index < 0 or packet_index >= len(packets):
                return {'success': False, 'error': 'Invalid packet index'}

            pkt = packets[packet_index]
            
            if not pkt.haslayer(TCP) or not pkt.haslayer(Raw):
                return {'success': False, 'error': 'Not a TLS packet'}
            
            payload = bytearray(pkt[Raw].load)
            
            # Check for TLS Client Hello
            if len(payload) < 43 or payload[0] != 0x16:
                return {'success': False, 'error': 'Not a TLS Client Hello packet'}
            
            # Find and replace SNI
            result = self._replace_sni_in_payload(payload, new_sni)
            
            if not result['success']:
                return result
            
            # Update packet with modified payload
            pkt[Raw].load = bytes(result['payload'])
            
            # Update TLS record length
            new_record_len = len(result['payload']) - 5
            payload_bytes = bytearray(pkt[Raw].load)
            payload_bytes[3:5] = new_record_len.to_bytes(2, 'big')
            pkt[Raw].load = bytes(payload_bytes)
            
            # Recalculate checksums
            pkt = self._recalculate_checksums(pkt)
            
            # Convert PacketList to list, update, and write back
            packet_list = list(packets)
            packet_list[packet_index] = pkt
            
            # Write back to file
            wrpcap(modified_filepath, packet_list)
            return {'success': True, 'new_sni': new_sni, 'modified_filepath': modified_filepath}

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _replace_sni_in_payload(self, payload, new_sni):
        """Helper method to replace SNI in TLS payload"""
        try:
            pos = 5  # Start after TLS record header
            
            # Skip handshake type (1) + length (3)
            handshake_len_pos = pos + 1
            pos += 4
            
            # Skip version (2) + random (32)
            pos += 34
            
            if pos >= len(payload):
                return {'success': False, 'error': 'Invalid TLS structure'}
            
            # Session ID length
            session_id_len = payload[pos]
            pos += 1 + session_id_len
            
            if pos + 2 >= len(payload):
                return {'success': False, 'error': 'Invalid TLS structure'}
            
            # Cipher suites length
            cipher_len = int.from_bytes(payload[pos:pos+2], 'big')
            pos += 2 + cipher_len
            
            if pos + 1 >= len(payload):
                return {'success': False, 'error': 'Invalid TLS structure'}
            
            # Compression methods length
            comp_len = payload[pos]
            pos += 1 + comp_len
            
            if pos + 2 >= len(payload):
                return {'success': False, 'error': 'Invalid TLS structure'}
            
            # Extensions length position (clamp ext_end to the real payload)
            ext_len_pos = pos
            ext_len = int.from_bytes(payload[pos:pos+2], 'big')
            pos += 2

            # Parse extensions to find SNI. Use <= so the final extension whose
            # 4-byte header ends exactly at ext_end is still examined.
            ext_end = min(pos + ext_len, len(payload))
            while pos + 4 <= ext_end:
                ext_type = int.from_bytes(payload[pos:pos+2], 'big')
                ext_data_len = int.from_bytes(payload[pos+2:pos+4], 'big')

                # SNI extension type is 0x0000
                if ext_type == 0x0000:
                    # Found SNI extension (need 9 header bytes before the name)
                    if pos + 9 > len(payload):
                        return {'success': False, 'error': 'Truncated SNI extension'}
                    old_sni_len = int.from_bytes(payload[pos+7:pos+9], 'big')
                    new_sni_bytes = new_sni.encode('utf-8')
                    new_sni_len = len(new_sni_bytes)
                    
                    # Calculate length difference
                    len_diff = new_sni_len - old_sni_len
                    
                    # Build new payload
                    sni_start = pos + 9
                    new_payload = bytearray()
                    new_payload.extend(payload[:sni_start])
                    new_payload.extend(new_sni_bytes)
                    new_payload.extend(payload[sni_start + old_sni_len:])
                    
                    # Update lengths
                    # SNI length
                    new_payload[pos+7:pos+9] = new_sni_len.to_bytes(2, 'big')
                    # SNI list length
                    new_payload[pos+4:pos+6] = (new_sni_len + 3).to_bytes(2, 'big')
                    # SNI extension length
                    new_payload[pos+2:pos+4] = (new_sni_len + 5).to_bytes(2, 'big')
                    # Extensions length
                    new_ext_len = ext_len + len_diff
                    new_payload[ext_len_pos:ext_len_pos+2] = new_ext_len.to_bytes(2, 'big')
                    # Handshake length
                    old_handshake_len = int.from_bytes(new_payload[handshake_len_pos:handshake_len_pos+3], 'big')
                    new_handshake_len = old_handshake_len + len_diff
                    new_payload[handshake_len_pos:handshake_len_pos+3] = new_handshake_len.to_bytes(3, 'big')
                    
                    return {'success': True, 'payload': new_payload}
                
                pos += 4 + ext_data_len
            
            return {'success': False, 'error': 'No SNI extension found'}

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def modify_ip_addresses(self, filepath, packet_index, src_ip=None, dst_ip=None):
        """Modify source and/or destination IP addresses"""
        try:
            # Use modified file to preserve original
            modified_filepath = self._get_modified_filepath(filepath)
            packets = rdpcap(modified_filepath)
            
            if packet_index < 0 or packet_index >= len(packets):
                return {'success': False, 'error': 'Invalid packet index'}

            pkt = packets[packet_index]
            
            if not pkt.haslayer(IP) and not pkt.haslayer(IPv6):
                return {'success': False, 'error': 'Not an IP packet'}
            
            # Modify IPv4
            if pkt.haslayer(IP):
                if src_ip:
                    pkt[IP].src = src_ip
                if dst_ip:
                    pkt[IP].dst = dst_ip
            # Modify IPv6
            elif pkt.haslayer(IPv6):
                if src_ip:
                    pkt[IPv6].src = src_ip
                if dst_ip:
                    pkt[IPv6].dst = dst_ip
            
            # Recalculate checksums
            pkt = self._recalculate_checksums(pkt)
            
            # Convert PacketList to list, update, and write back
            packet_list = list(packets)
            packet_list[packet_index] = pkt
            
            # Write back to file
            wrpcap(modified_filepath, packet_list)
            return {'success': True, 'src_ip': src_ip, 'dst_ip': dst_ip, 'modified_filepath': modified_filepath}

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def modify_ports(self, filepath, packet_index, src_port=None, dst_port=None):
        """Modify source and/or destination ports"""
        try:
            # Use modified file to preserve original
            modified_filepath = self._get_modified_filepath(filepath)
            packets = rdpcap(modified_filepath)
            
            if packet_index < 0 or packet_index >= len(packets):
                return {'success': False, 'error': 'Invalid packet index'}

            pkt = packets[packet_index]
            
            if not pkt.haslayer(TCP) and not pkt.haslayer(UDP):
                return {'success': False, 'error': 'Not a TCP/UDP packet'}
            
            # Modify TCP ports
            if pkt.haslayer(TCP):
                if src_port:
                    pkt[TCP].sport = int(src_port)
                if dst_port:
                    pkt[TCP].dport = int(dst_port)
            # Modify UDP ports
            elif pkt.haslayer(UDP):
                if src_port:
                    pkt[UDP].sport = int(src_port)
                if dst_port:
                    pkt[UDP].dport = int(dst_port)
            
            # Recalculate checksums
            pkt = self._recalculate_checksums(pkt)
            
            # Convert PacketList to list, update, and write back
            packet_list = list(packets)
            packet_list[packet_index] = pkt
            
            # Write back to file
            wrpcap(modified_filepath, packet_list)
            return {'success': True, 'src_port': src_port, 'dst_port': dst_port, 'modified_filepath': modified_filepath}

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def modify_mac_addresses(self, filepath, packet_index, src_mac=None, dst_mac=None):
        """Modify source and/or destination MAC addresses"""
        try:
            # Use modified file to preserve original
            modified_filepath = self._get_modified_filepath(filepath)
            packets = rdpcap(modified_filepath)
            
            if packet_index < 0 or packet_index >= len(packets):
                return {'success': False, 'error': 'Invalid packet index'}

            pkt = packets[packet_index]
            
            if not pkt.haslayer(Ether):
                return {'success': False, 'error': 'No Ethernet layer found'}
            
            if src_mac:
                pkt[Ether].src = src_mac
            if dst_mac:
                pkt[Ether].dst = dst_mac
            
            # Recalculate checksums
            pkt = self._recalculate_checksums(pkt)
            
            # Convert PacketList to list, update, and write back
            packet_list = list(packets)
            packet_list[packet_index] = pkt
            
            # Write back to file
            wrpcap(modified_filepath, packet_list)
            return {'success': True, 'src_mac': src_mac, 'dst_mac': dst_mac, 'modified_filepath': modified_filepath}

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def modify_vlan(self, filepath, packet_index, vlan_id):
        """Modify VLAN ID"""
        try:
            # Use modified file to preserve original
            modified_filepath = self._get_modified_filepath(filepath)
            packets = rdpcap(modified_filepath)
            
            if packet_index < 0 or packet_index >= len(packets):
                return {'success': False, 'error': 'Invalid packet index'}

            pkt = packets[packet_index]
            
            if not pkt.haslayer(Dot1Q):
                return {'success': False, 'error': 'No VLAN tag found'}
            
            pkt[Dot1Q].vlan = int(vlan_id)
            
            # Recalculate checksums
            pkt = self._recalculate_checksums(pkt)
            
            # Convert PacketList to list, update, and write back
            packet_list = list(packets)
            packet_list[packet_index] = pkt
            
            # Write back to file
            wrpcap(modified_filepath, packet_list)
            return {'success': True, 'vlan_id': vlan_id, 'modified_filepath': modified_filepath}

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def add_vlan(self, filepath, packet_index, vlan_id, priority=0):
        """Add VLAN tag to packet"""
        try:
            # Use modified file to preserve original
            modified_filepath = self._get_modified_filepath(filepath)
            packets = rdpcap(modified_filepath)
            
            if packet_index < 0 or packet_index >= len(packets):
                return {'success': False, 'error': 'Invalid packet index'}

            pkt = packets[packet_index]
            
            if not pkt.haslayer(Ether):
                return {'success': False, 'error': 'No Ethernet layer found'}
            
            if pkt.haslayer(Dot1Q):
                return {'success': False, 'error': 'VLAN tag already exists'}
            
            # Insert VLAN tag between Ether and payload
            ether = pkt[Ether]
            payload = ether.payload
            
            # Create new packet with VLAN tag
            new_pkt = Ether(src=ether.src, dst=ether.dst) / Dot1Q(vlan=int(vlan_id), prio=int(priority)) / payload
            
            # Preserve timestamp if exists
            if hasattr(pkt, 'time'):
                new_pkt.time = pkt.time
            
            # Recalculate checksums
            new_pkt = self._recalculate_checksums(new_pkt)
            
            # Convert PacketList to list, update, and write back
            packet_list = list(packets)
            packet_list[packet_index] = new_pkt
            
            # Write back to file
            wrpcap(modified_filepath, packet_list)
            return {'success': True, 'vlan_id': vlan_id, 'priority': priority, 'modified_filepath': modified_filepath}

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def get_dns_query(self, filepath, packet_index):
        """Extract DNS query from packet (TCP or UDP)"""
        try:
            packets = self._read(filepath)
            
            if packet_index < 0 or packet_index >= len(packets):
                return None

            pkt = packets[packet_index]
            
            # Check for DNS layer
            if not pkt.haslayer(DNS):
                return None
            
            dns_layer = pkt[DNS]
            
            # Extract query name from the first question
            if dns_layer.qdcount > 0 and dns_layer.qd:
                query_name = dns_layer.qd.qname.decode('utf-8', errors='ignore').rstrip('.')
                return query_name
            
            return None

        except Exception as e:
            return None

    def modify_dns_query(self, filepath, packet_index, new_query):
        """Modify DNS query in packet (TCP or UDP)"""
        try:
            # Use modified file to preserve original
            modified_filepath = self._get_modified_filepath(filepath)
            packets = rdpcap(modified_filepath)
            
            if packet_index < 0 or packet_index >= len(packets):
                return {'success': False, 'error': 'Invalid packet index'}

            pkt = packets[packet_index]
            
            if not pkt.haslayer(DNS):
                return {'success': False, 'error': 'No DNS layer found'}
            
            # Get original DNS layer
            dns_layer = pkt[DNS]
            
            if dns_layer.qdcount == 0 or not dns_layer.qd:
                return {'success': False, 'error': 'No DNS query found'}
            
            # Ensure query ends with a dot for FQDN
            if not new_query.endswith('.'):
                new_query = new_query + '.'
            
            # Get the query type and class from the original query
            query_type = dns_layer.qd.qtype if hasattr(dns_layer.qd, 'qtype') else 1
            query_class = dns_layer.qd.qclass if hasattr(dns_layer.qd, 'qclass') else 1
            
            # Create new DNS layer with modified query
            new_dns = DNS(
                id=dns_layer.id,
                qr=dns_layer.qr,
                opcode=dns_layer.opcode,
                aa=dns_layer.aa,
                tc=dns_layer.tc,
                rd=dns_layer.rd,
                ra=dns_layer.ra,
                z=dns_layer.z,
                rcode=dns_layer.rcode,
                qdcount=1,
                ancount=dns_layer.ancount,
                nscount=dns_layer.nscount,
                arcount=dns_layer.arcount,
                qd=DNSQR(qname=new_query, qtype=query_type, qclass=query_class)
            )
            
            # Copy answer records if present
            if dns_layer.ancount > 0 and dns_layer.an:
                new_dns.an = dns_layer.an
            if dns_layer.nscount > 0 and dns_layer.ns:
                new_dns.ns = dns_layer.ns
            if dns_layer.arcount > 0 and dns_layer.ar:
                new_dns.ar = dns_layer.ar
            
            # Rebuild packet with all layers
            new_pkt = None
            
            # Start with Ethernet layer if present
            if pkt.haslayer(Ether):
                new_pkt = Ether(src=pkt[Ether].src, dst=pkt[Ether].dst, type=pkt[Ether].type)
            
            # Add VLAN if present
            if pkt.haslayer(Dot1Q):
                vlan = Dot1Q(vlan=pkt[Dot1Q].vlan, type=pkt[Dot1Q].type)
                new_pkt = new_pkt / vlan if new_pkt else vlan
            
            # Add IP layer
            if pkt.haslayer(IP):
                ip = IP(src=pkt[IP].src, dst=pkt[IP].dst, proto=pkt[IP].proto)
                new_pkt = new_pkt / ip if new_pkt else ip
            elif pkt.haslayer(IPv6):
                ip = IPv6(src=pkt[IPv6].src, dst=pkt[IPv6].dst, nh=pkt[IPv6].nh)
                new_pkt = new_pkt / ip if new_pkt else ip
            
            # Add TCP/UDP layer
            if pkt.haslayer(TCP):
                tcp = TCP(sport=pkt[TCP].sport, dport=pkt[TCP].dport, flags=pkt[TCP].flags)
                new_pkt = new_pkt / tcp if new_pkt else tcp
            elif pkt.haslayer(UDP):
                udp = UDP(sport=pkt[UDP].sport, dport=pkt[UDP].dport)
                new_pkt = new_pkt / udp if new_pkt else udp
            
            # Add the new DNS layer
            new_pkt = new_pkt / new_dns if new_pkt else new_dns
            
            # Recalculate checksums
            new_pkt = self._recalculate_checksums(new_pkt)
            
            # Convert PacketList to list, update, and write back
            packet_list = list(packets)
            packet_list[packet_index] = new_pkt
            
            # Write back to file
            wrpcap(modified_filepath, packet_list)
            return {'success': True, 'new_query': new_query.rstrip('.'), 'modified_filepath': modified_filepath}

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def analyze_packet_for_editing(self, filepath, packet_index):
        """Analyze packet to determine editable fields"""
        try:
            packets = self._read(filepath)
            
            if packet_index < 0 or packet_index >= len(packets):
                return {'editable': False}

            pkt = packets[packet_index]
            
            result = {
                'editable': False,
                'http_host': None,
                'tls_sni': None,
                'dns_query': None,
                'src_mac': None,
                'dst_mac': None,
                'src_ip': None,
                'dst_ip': None,
                'src_port': None,
                'dst_port': None,
                'vlan_id': None,
                'has_vlan': False
            }
            
            # MAC addresses
            if pkt.haslayer(Ether):
                result['src_mac'] = pkt[Ether].src
                result['dst_mac'] = pkt[Ether].dst
                result['editable'] = True
            
            # VLAN
            if pkt.haslayer(Dot1Q):
                result['vlan_id'] = pkt[Dot1Q].vlan
                result['has_vlan'] = True
                result['editable'] = True
            
            # IP addresses
            if pkt.haslayer(IP):
                result['src_ip'] = pkt[IP].src
                result['dst_ip'] = pkt[IP].dst
                result['editable'] = True
            elif pkt.haslayer(IPv6):
                result['src_ip'] = pkt[IPv6].src
                result['dst_ip'] = pkt[IPv6].dst
                result['editable'] = True
            
            # Ports
            if pkt.haslayer(TCP):
                result['src_port'] = pkt[TCP].sport
                result['dst_port'] = pkt[TCP].dport
                result['editable'] = True
            elif pkt.haslayer(UDP):
                result['src_port'] = pkt[UDP].sport
                result['dst_port'] = pkt[UDP].dport
                result['editable'] = True
            
            # Check for HTTP Host
            host = self.get_http_host(filepath, packet_index)
            if host:
                result['http_host'] = host
            
            # Check for TLS SNI
            sni = self.get_tls_sni(filepath, packet_index)
            if sni:
                result['tls_sni'] = sni
            
            # Check for DNS Query
            dns_query = self.get_dns_query(filepath, packet_index)
            if dns_query:
                result['dns_query'] = dns_query
            
            return result
        
        except Exception as e:
            return {'editable': False, 'error': str(e)}

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

    # -------------------------------------------------------------------------
    # Bulk / Structural packet operations
    # -------------------------------------------------------------------------

    def bulk_modify_packets(self, filepath, packet_indices, fields, incremental=None, keep_unselected=True):
        """
        Modify selected packets in bulk.
        packet_indices: list of int indices, or None to modify all packets.
        fields: dict with any of src_ip, dst_ip, src_mac, dst_mac,
                src_port, dst_port, vlan_id.
        incremental: optional dict:
            {
                'enabled': True,
                'step': 1,
                'fields': ['src_ip', 'dst_ip', 'src_port', 'dst_port']
            }
            When enabled, the listed fields are incremented by step*i
            for the i-th selected packet (i=0,1,2,...)
        keep_unselected: bool, if False, only the packets in packet_indices are kept.
        """
        import ipaddress as _ipaddr
        try:
            modified_filepath = self._get_modified_filepath(filepath)
            packets = rdpcap(modified_filepath)
            n = len(packets)
            indices = list(range(n)) if packet_indices is None else [
                i for i in packet_indices if 0 <= i < n
            ]
            packet_list = list(packets)
            modified_count = 0
            errors = []

            # Resolve incremental configuration
            inc_enabled = bool(incremental and incremental.get('enabled', False))
            inc_step = int(incremental.get('step', 1)) if incremental else 1
            inc_fields = set(incremental.get('fields', [])) if incremental else set()

            # Pre-parse base IP addresses for increment
            base_src_ip = None
            base_dst_ip = None
            if inc_enabled:
                if 'src_ip' in inc_fields and fields.get('src_ip'):
                    try:
                        base_src_ip = _ipaddr.ip_address(fields['src_ip'])
                    except Exception:
                        pass
                if 'dst_ip' in inc_fields and fields.get('dst_ip'):
                    try:
                        base_dst_ip = _ipaddr.ip_address(fields['dst_ip'])
                    except Exception:
                        pass

            for i, idx in enumerate(indices):
                pkt = packet_list[idx]
                changed = False
                try:
                    # Compute effective values for this packet
                    eff = dict(fields)
                    if inc_enabled:
                        if base_src_ip is not None:
                            eff['src_ip'] = str(base_src_ip + i * inc_step)
                        if base_dst_ip is not None:
                            eff['dst_ip'] = str(base_dst_ip + i * inc_step)
                        if 'src_port' in inc_fields and eff.get('src_port') is not None:
                            raw = int(eff['src_port']) + i * inc_step
                            eff['src_port'] = ((raw - 1) % 65535) + 1  # wrap 1-65535
                        if 'dst_port' in inc_fields and eff.get('dst_port') is not None:
                            raw = int(eff['dst_port']) + i * inc_step
                            eff['dst_port'] = ((raw - 1) % 65535) + 1

                    if pkt.haslayer(Ether):
                        if eff.get('src_mac'):
                            pkt[Ether].src = eff['src_mac']
                            changed = True
                        if eff.get('dst_mac'):
                            pkt[Ether].dst = eff['dst_mac']
                            changed = True

                    if pkt.haslayer(Dot1Q) and eff.get('vlan_id') is not None:
                        pkt[Dot1Q].vlan = int(eff['vlan_id'])
                        changed = True

                    if pkt.haslayer(IP):
                        if eff.get('src_ip'):
                            pkt[IP].src = eff['src_ip']
                            changed = True
                        if eff.get('dst_ip'):
                            pkt[IP].dst = eff['dst_ip']
                            changed = True
                    elif pkt.haslayer(IPv6):
                        if eff.get('src_ip'):
                            pkt[IPv6].src = eff['src_ip']
                            changed = True
                        if eff.get('dst_ip'):
                            pkt[IPv6].dst = eff['dst_ip']
                            changed = True

                    if pkt.haslayer(TCP):
                        if eff.get('src_port') is not None:
                            pkt[TCP].sport = int(eff['src_port'])
                            changed = True
                        if eff.get('dst_port') is not None:
                            pkt[TCP].dport = int(eff['dst_port'])
                            changed = True
                    elif pkt.haslayer(UDP):
                        if eff.get('src_port') is not None:
                            pkt[UDP].sport = int(eff['src_port'])
                            changed = True
                        if eff.get('dst_port') is not None:
                            pkt[UDP].dport = int(eff['dst_port'])
                            changed = True

                    if changed:
                        pkt = self._recalculate_checksums(pkt)
                        packet_list[idx] = pkt
                        modified_count += 1
                except Exception as e:
                    errors.append(f'Packet {idx}: {str(e)}')

            # If keep_unselected is False, filter the list to only include modified/selected indices
            if not keep_unselected and packet_indices is not None:
                # To maintain order, we use the original indices but only those in the packet_indices list
                packet_list = [packet_list[i] for i in sorted(set(indices))]

            wrpcap(modified_filepath, packet_list)
            return {
                'success': True,
                'modified_count': modified_count,
                'total_selected': len(indices),
                'new_total_count': len(packet_list),
                'errors': errors,
                'modified_filepath': modified_filepath
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def delete_packet(self, filepath, packet_index):
        """Delete a packet at the given index."""
        try:
            modified_filepath = self._get_modified_filepath(filepath)
            packets = rdpcap(modified_filepath)
            if packet_index < 0 or packet_index >= len(packets):
                return {'success': False, 'error': 'Invalid packet index'}
            packet_list = list(packets)
            del packet_list[packet_index]
            wrpcap(modified_filepath, packet_list)
            return {
                'success': True,
                'new_packet_count': len(packet_list),
                'modified_filepath': modified_filepath
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def duplicate_packet(self, filepath, packet_index):
        """Duplicate a packet, inserting the copy right after the original."""
        try:
            modified_filepath = self._get_modified_filepath(filepath)
            packets = rdpcap(modified_filepath)
            if packet_index < 0 or packet_index >= len(packets):
                return {'success': False, 'error': 'Invalid packet index'}
            packet_list = list(packets)
            original = packet_list[packet_index]
            # Deep copy via re-parsing bytes
            duplicate = original.__class__(bytes(original))
            if hasattr(original, 'time'):
                duplicate.time = original.time
            packet_list.insert(packet_index + 1, duplicate)
            wrpcap(modified_filepath, packet_list)
            return {
                'success': True,
                'new_packet_count': len(packet_list),
                'new_index': packet_index + 1,
                'modified_filepath': modified_filepath
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def move_packet(self, filepath, packet_index, direction):
        """Move a packet: direction is 'up', 'down', 'top', or 'bottom'."""
        try:
            modified_filepath = self._get_modified_filepath(filepath)
            packets = rdpcap(modified_filepath)
            n = len(packets)
            if packet_index < 0 or packet_index >= n:
                return {'success': False, 'error': 'Invalid packet index'}
            packet_list = list(packets)
            pkt = packet_list.pop(packet_index)
            if direction == 'up':
                new_index = max(0, packet_index - 1)
            elif direction == 'down':
                new_index = min(n - 1, packet_index + 1)
            elif direction == 'top':
                new_index = 0
            elif direction == 'bottom':
                new_index = n - 1
            else:
                packet_list.insert(packet_index, pkt)
                return {'success': False, 'error': f'Invalid direction: {direction}'}
            packet_list.insert(new_index, pkt)
            wrpcap(modified_filepath, packet_list)
            return {
                'success': True,
                'new_index': new_index,
                'modified_filepath': modified_filepath
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def replicate_packets(self, filepath, packet_indices, count):
        """
        Replicate selected packets `count` times.
        Copies are inserted immediately after the last selected packet,
        in rounds: [round1_p0, round1_p1, ...], [round2_p0, round2_p1, ...], ...
        Original packets are preserved unchanged.
        Returns new_indices: flat list of indices of all newly created copies.
        """
        try:
            modified_filepath = self._get_modified_filepath(filepath)
            packets = rdpcap(modified_filepath)
            n = len(packets)

            valid_indices = sorted(set(
                i for i in packet_indices if 0 <= i < n
            ))
            if not valid_indices:
                return {'success': False, 'error': 'No valid packet indices provided'}

            packet_list = list(packets)
            insert_after = max(valid_indices)
            selected_pkts = [packet_list[i] for i in valid_indices]

            # Build all copies: `count` rounds of the full selection sequence
            all_copies = []
            for _round in range(count):
                for orig in selected_pkts:
                    dup = orig.__class__(bytes(orig))
                    if hasattr(orig, 'time'):
                        dup.time = orig.time
                    all_copies.append(dup)

            new_list = (
                packet_list[:insert_after + 1]
                + all_copies
                + packet_list[insert_after + 1:]
            )

            new_copy_start = insert_after + 1
            new_indices = list(range(new_copy_start, new_copy_start + len(all_copies)))

            wrpcap(modified_filepath, new_list)
            return {
                'success': True,
                'new_packet_count': len(new_list),
                'copy_count': len(all_copies),
                'new_indices': new_indices,
                'modified_filepath': modified_filepath
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def extract_packets(self, filepath, packet_indices):
        """
        Extract the selected packets into a brand-new PCAP file, preserving
        capture order. The source file is left untouched (no mutation).
        Returns the new file's path, name and packet count.
        """
        try:
            from datetime import datetime

            packets = self._read(filepath)
            n = len(packets)

            valid_indices = sorted(set(
                i for i in packet_indices if isinstance(i, int) and 0 <= i < n
            ))
            if not valid_indices:
                return {'success': False, 'error': 'No valid packet indices provided'}

            extracted = [packets[i] for i in valid_indices]

            # Derive a clean output name from the (de-modified) source name
            base = os.path.basename(filepath)
            if base.startswith('modified_'):
                base = base[len('modified_'):]
            name, _ext = os.path.splitext(base)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            out_name = f'extracted_{len(valid_indices)}pkts_{timestamp}_{name}.pcap'
            out_path = os.path.join(self.upload_folder, out_name)

            wrpcap(out_path, extracted)
            return {
                'success': True,
                'filepath': out_path,
                'filename': out_name,
                'packet_count': len(extracted),
                'source_indices': valid_indices
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

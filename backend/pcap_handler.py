"""
PCAP file handler
Manages reading, writing, and modifying PCAP files using Scapy
"""

import os
import shutil
from scapy.all import rdpcap, wrpcap, IP, IPv6, TCP, UDP, ICMP, Raw, Ether, Dot1Q, DNS, DNSQR, DNSRR
from collections import defaultdict
import binascii
import re


class PCAPHandler:
    """Handler for PCAP file operations"""

    def __init__(self, upload_folder='uploads'):
        """Initialize PCAP handler with upload folder"""
        self.upload_folder = upload_folder

    def _get_modified_filepath(self, filepath):
        """Get the path for modified file, creating it if necessary"""
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
            packets = rdpcap(filepath)
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
            packets = rdpcap(filepath)
            
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
            packets = rdpcap(filepath)
            
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

            # Write back to file
            wrpcap(filepath, packets)
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
            packets = rdpcap(filepath)
            
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

                # Protocol statistics
                if pkt.haslayer(IP):
                    stats['protocols']['IPv4'] += 1
                    src_ip = pkt[IP].src
                    dst_ip = pkt[IP].dst
                    stats['src_ips'][src_ip] += 1
                    stats['dst_ips'][dst_ip] += 1

                elif pkt.haslayer(IPv6):
                    stats['protocols']['IPv6'] += 1

                if pkt.haslayer(TCP):
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
        except:
            return pkt

    def _reconstruct_packet(self, pkt_data):
        """Reconstruct packet from data dictionary"""
        try:
            # This is a simplified version - can be expanded based on data format
            return None
        except:
            return None

    def get_http_host(self, filepath, packet_index):
        """Extract HTTP HOST header from packet"""
        try:
            packets = rdpcap(filepath)
            
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
            packets = rdpcap(filepath)
            
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
            
            # Extensions length
            ext_len = int.from_bytes(payload[pos:pos+2], 'big')
            pos += 2
            
            # Parse extensions to find SNI
            ext_end = pos + ext_len
            while pos + 4 < ext_end:
                ext_type = int.from_bytes(payload[pos:pos+2], 'big')
                ext_data_len = int.from_bytes(payload[pos+2:pos+4], 'big')
                pos += 4
                
                # SNI extension type is 0x0000
                if ext_type == 0x0000:
                    # SNI extension found
                    if pos + 5 < len(payload):
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
            
            # Extensions length position
            ext_len_pos = pos
            ext_len = int.from_bytes(payload[pos:pos+2], 'big')
            pos += 2
            
            # Parse extensions to find SNI
            ext_end = pos + ext_len
            while pos + 4 < ext_end:
                ext_type = int.from_bytes(payload[pos:pos+2], 'big')
                ext_data_len = int.from_bytes(payload[pos+2:pos+4], 'big')
                
                # SNI extension type is 0x0000
                if ext_type == 0x0000:
                    # Found SNI extension
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
            packets = rdpcap(filepath)
            
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
            packets = rdpcap(filepath)
            
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
            src_ip = options.get('src_ip', '192.168.1.100')
            base_dst_ip = options.get('dst_ip', '192.168.1.200')
            src_port = options.get('src_port', random.randint(49152, 65535))
            dst_port = options.get('dst_port', 80)
            
            # Parse base destination IP to allow incrementing
            try:
                base_dst_ip_obj = ipaddress.ip_address(base_dst_ip)
            except ValueError:
                base_dst_ip_obj = ipaddress.ip_address('192.168.1.200')
            
            for i in range(packet_count):
                # Increment destination IP for each packet
                current_dst_ip = str(base_dst_ip_obj + i)
                # Use different source ports for each flow
                current_src_port = src_port + i
                
                # Generate based on protocol
                if protocol == 'tcp' or protocol == 'http' or protocol == 'tls':
                    # Generate complete TCP flow for TCP-based protocols
                    flow_packets = self._generate_tcp_flow(
                        src_mac, dst_mac, src_ip, current_dst_ip,
                        current_src_port, dst_port if protocol == 'tcp' else (80 if protocol == 'http' else 443),
                        protocol, vlan_id, i, options
                    )
                    packets.extend(flow_packets)
                
                elif protocol == 'udp':
                    # Build Ethernet layer
                    eth = Ether(src=src_mac, dst=dst_mac)
                    if vlan_id is not None:
                        eth = eth / Dot1Q(vlan=vlan_id)
                    
                    # UDP doesn't need full flow - single packet
                    pkt = eth / IP(src=src_ip, dst=current_dst_ip) / UDP(sport=current_src_port, dport=dst_port) / Raw(load=f"UDP Packet {i+1}")
                    packets.append(pkt)
                
                elif protocol == 'dns_udp':
                    # Build Ethernet layer
                    eth = Ether(src=src_mac, dst=dst_mac)
                    if vlan_id is not None:
                        eth = eth / Dot1Q(vlan=vlan_id)
                    
                    dns_query = options.get('dns_query', 'example.com')
                    # DNS Query
                    query_pkt = eth / IP(src=src_ip, dst=current_dst_ip) / UDP(sport=current_src_port, dport=53) / DNS(rd=1, qd=DNSQR(qname=dns_query))
                    packets.append(query_pkt)
                    
                    # DNS Response
                    response_pkt = eth / IP(src=current_dst_ip, dst=src_ip) / UDP(sport=53, dport=current_src_port) / DNS(
                        id=query_pkt[DNS].id, qr=1, aa=1, qd=DNSQR(qname=dns_query), 
                        an=DNSRR(rrname=dns_query, ttl=300, rdata=current_dst_ip)
                    )
                    packets.append(response_pkt)
                
                elif protocol == 'dns_tcp':
                    # Generate complete TCP flow with DNS payload
                    flow_packets = self._generate_tcp_flow(
                        src_mac, dst_mac, src_ip, current_dst_ip,
                        current_src_port, 53, protocol, vlan_id, i, options
                    )
                    packets.extend(flow_packets)
                
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
                # Resolve relative paths against upload folder when needed
                resolved_path = fp
                if not os.path.isabs(resolved_path) and not os.path.exists(resolved_path):
                    resolved_path = os.path.join(self.upload_folder, os.path.basename(fp))

                if not os.path.exists(resolved_path):
                    return {'success': False, 'error': f'File not found: {fp}'}

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

    def _generate_tcp_flow(self, src_mac, dst_mac, src_ip, dst_ip, src_port, dst_port, protocol, vlan_id, index, options):
        """Generate a complete TCP 3-way handshake, data exchange, and connection termination"""
        import random
        
        flow_packets = []
        
        # Initial sequence numbers
        client_seq = random.randint(1000, 100000)
        server_seq = random.randint(1000, 100000)
        
        # Build base Ethernet layer
        def build_eth():
            eth = Ether(src=src_mac, dst=dst_mac)
            if vlan_id is not None:
                eth = eth / Dot1Q(vlan=vlan_id)
            return eth
        
        # 1. SYN: Client initiates connection
        syn_pkt = build_eth() / IP(src=src_ip, dst=dst_ip) / TCP(sport=src_port, dport=dst_port, flags='S', seq=client_seq)
        flow_packets.append(syn_pkt)
        
        # 2. SYN-ACK: Server acknowledges and sends its SYN
        synack_pkt = build_eth() / IP(src=dst_ip, dst=src_ip) / TCP(sport=dst_port, dport=src_port, flags='SA', seq=server_seq, ack=client_seq + 1)
        flow_packets.append(synack_pkt)
        
        # 3. ACK: Client acknowledges server's SYN
        ack_pkt = build_eth() / IP(src=src_ip, dst=dst_ip) / TCP(sport=src_port, dport=dst_port, flags='A', seq=client_seq + 1, ack=server_seq + 1)
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
            data_pkt = build_eth() / IP(src=src_ip, dst=dst_ip) / TCP(sport=src_port, dport=dst_port, flags='PA', seq=client_seq + 1, ack=server_seq + 1) / Raw(load=payload)
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
            response_pkt = build_eth() / IP(src=dst_ip, dst=src_ip) / TCP(sport=dst_port, dport=src_port, flags='PA', seq=server_seq + 1, ack=client_seq + 1 + len(payload)) / Raw(load=response_payload)
            flow_packets.append(response_pkt)
            
            # Client ACK for response
            ack_response = build_eth() / IP(src=src_ip, dst=dst_ip) / TCP(sport=src_port, dport=dst_port, flags='A', seq=client_seq + 1 + len(payload), ack=server_seq + 1 + len(response_payload))
            flow_packets.append(ack_response)
            
            client_seq += len(payload)
            server_seq += len(response_payload)
            
        elif protocol == 'tls':
            # TLS Client Hello
            sni = options.get('tls_sni', 'example.com')
            tls_hello = self._build_tls_client_hello(sni)
            tls_pkt = build_eth() / IP(src=src_ip, dst=dst_ip) / TCP(sport=src_port, dport=dst_port, flags='PA', seq=client_seq + 1, ack=server_seq + 1) / Raw(load=tls_hello)
            flow_packets.append(tls_pkt)
            
            # TLS Server Hello (simplified)
            server_hello = b'\x16\x03\x03\x00\x31' + bytes([0x00] * 49)  # Minimal TLS Server Hello
            tls_response = build_eth() / IP(src=dst_ip, dst=src_ip) / TCP(sport=dst_port, dport=src_port, flags='PA', seq=server_seq + 1, ack=client_seq + 1 + len(tls_hello)) / Raw(load=server_hello)
            flow_packets.append(tls_response)
            
            client_seq += len(tls_hello)
            server_seq += len(server_hello)
            
        elif protocol == 'dns_tcp':
            dns_query = options.get('dns_query', 'example.com')
            dns = DNS(rd=1, qd=DNSQR(qname=dns_query))
            dns_bytes = bytes(dns)
            dns_len = len(dns_bytes).to_bytes(2, 'big')
            payload = dns_len + dns_bytes
            
            data_pkt = build_eth() / IP(src=src_ip, dst=dst_ip) / TCP(sport=src_port, dport=dst_port, flags='PA', seq=client_seq + 1, ack=server_seq + 1) / Raw(load=payload)
            flow_packets.append(data_pkt)
            
            # DNS Response
            dns_response = DNS(id=dns.id, qr=1, aa=1, qd=DNSQR(qname=dns_query), an=DNSRR(rrname=dns_query, ttl=300, rdata=dst_ip))
            dns_response_bytes = bytes(dns_response)
            dns_response_len = len(dns_response_bytes).to_bytes(2, 'big')
            response_payload = dns_response_len + dns_response_bytes
            
            response_pkt = build_eth() / IP(src=dst_ip, dst=src_ip) / TCP(sport=dst_port, dport=src_port, flags='PA', seq=server_seq + 1, ack=client_seq + 1 + len(payload)) / Raw(load=response_payload)
            flow_packets.append(response_pkt)
            
            client_seq += len(payload)
            server_seq += len(response_payload)
            
        else:  # tcp
            payload = f"TCP Data Packet {index + 1}".encode()
            data_pkt = build_eth() / IP(src=src_ip, dst=dst_ip) / TCP(sport=src_port, dport=dst_port, flags='PA', seq=client_seq + 1, ack=server_seq + 1) / Raw(load=payload)
            flow_packets.append(data_pkt)
            
            # Server ACK
            ack_data = build_eth() / IP(src=dst_ip, dst=src_ip) / TCP(sport=dst_port, dport=src_port, flags='A', seq=server_seq + 1, ack=client_seq + 1 + len(payload))
            flow_packets.append(ack_data)
            
            client_seq += len(payload)
        
        # 5. FIN: Client initiates connection close
        fin_pkt = build_eth() / IP(src=src_ip, dst=dst_ip) / TCP(sport=src_port, dport=dst_port, flags='FA', seq=client_seq + 1, ack=server_seq + 1)
        flow_packets.append(fin_pkt)
        
        # 6. ACK: Server acknowledges FIN
        ack_fin_pkt = build_eth() / IP(src=dst_ip, dst=src_ip) / TCP(sport=dst_port, dport=src_port, flags='A', seq=server_seq + 1, ack=client_seq + 2)
        flow_packets.append(ack_fin_pkt)
        
        # 7. FIN: Server sends its FIN
        fin_server_pkt = build_eth() / IP(src=dst_ip, dst=src_ip) / TCP(sport=dst_port, dport=src_port, flags='FA', seq=server_seq + 1, ack=client_seq + 2)
        flow_packets.append(fin_server_pkt)
        
        # 8. ACK: Client acknowledges server's FIN
        final_ack_pkt = build_eth() / IP(src=src_ip, dst=dst_ip) / TCP(sport=src_port, dport=dst_port, flags='A', seq=client_seq + 2, ack=server_seq + 2)
        flow_packets.append(final_ack_pkt)
        
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

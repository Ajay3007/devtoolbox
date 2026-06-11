"""
PCAP Editor Backend API
Handles PCAP file operations including reading, writing, and payload modification
"""

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from werkzeug.utils import secure_filename
import os
import json
from datetime import datetime
from pcap_handler import PCAPHandler
from pdf_handler import PDFHandler
try:
    from receipt_handler import ReceiptHandler
    _RECEIPT_AVAILABLE = True
except ImportError:
    ReceiptHandler = None
    _RECEIPT_AVAILABLE = False
from utils import (
    generate_response, allowed_file, resolve_upload_path,
    validate_network_fields, validate_vlan,
)

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pcap', 'pcapng'}
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB

# Create Flask app
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

# Enable CORS for frontend communication
CORS(app)

# Create upload folder if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Initialize handlers
pcap_handler     = PCAPHandler(UPLOAD_FOLDER)
pdf_handler      = PDFHandler(UPLOAD_FOLDER)
receipt_handler  = ReceiptHandler(UPLOAD_FOLDER) if _RECEIPT_AVAILABLE else None


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'PCAP Editor API',
        'timestamp': datetime.now().isoformat()
    })


@app.route('/api/pcap/upload', methods=['POST'])
def upload_pcap():
    """
    Upload a PCAP file
    Returns: List of packets in the file
    """
    try:
        if 'file' not in request.files:
            return generate_response('No file provided', 400, False)

        file = request.files['file']
        
        if file.filename == '':
            return generate_response('No file selected', 400, False)

        if not allowed_file(file.filename, ALLOWED_EXTENSIONS):
            return generate_response('Invalid file type. Only .pcap and .pcapng allowed', 400, False)

        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], timestamp + filename)

        # Save file
        file.save(filepath)

        # Parse PCAP file
        packets = pcap_handler.read_pcap(filepath)
        
        return generate_response(
            {
                'filepath': filepath.replace('\\', '/'),
                'filename': filename,
                'packet_count': len(packets),
                'packets': packets[:100]  # Return first 100 packets for preview
            },
            200,
            True
        )

    except Exception as e:
        return generate_response(f'Error uploading file: {str(e)}', 500, False)


@app.route('/api/pcap/packets/<path:filepath>', methods=['GET'])
def get_packets(filepath):
    """
    Get all packets from a PCAP file
    Query params: offset, limit
    """
    try:
        offset = request.args.get('offset', default=0, type=int)
        limit = request.args.get('limit', default=100, type=int)

        packets = pcap_handler.read_pcap(filepath)
        total = len(packets)
        
        # Pagination
        paginated_packets = packets[offset:offset + limit]

        return generate_response(
            {
                'total': total,
                'offset': offset,
                'limit': limit,
                'packets': paginated_packets
            },
            200,
            True
        )

    except Exception as e:
        return generate_response(f'Error retrieving packets: {str(e)}', 500, False)


@app.route('/api/pcap/<path:filepath>', methods=['GET'])
def get_pcap_file(filepath):
    """
    Get complete PCAP file information including packets and statistics
    """
    try:
        # Resolve + contain the path before any filesystem access
        file_path = resolve_upload_path(filepath, app.config['UPLOAD_FOLDER'], must_exist=True)

        # Read packets
        packets = pcap_handler.read_pcap(filepath)

        file_size = os.path.getsize(file_path)

        # Calculate statistics
        stats = pcap_handler.get_statistics(filepath)
        
        return jsonify({
            'success': True,
            'file': {
                'name': filepath,
                'size': file_size
            },
            'packets': packets,
            'statistics': stats
        })
    
    except Exception as e:
        return generate_response(f'Error loading file: {str(e)}', 500, False)


@app.route('/api/pcap/packet/<path:filepath>/<int:packet_index>', methods=['GET'])
def get_packet_details(filepath, packet_index):
    """Get detailed information about a specific packet"""
    try:
        packet = pcap_handler.get_packet_details(filepath, packet_index)
        
        if packet is None:
            return generate_response('Packet not found', 404, False)

        return generate_response(packet, 200, True)

    except Exception as e:
        return generate_response(f'Error retrieving packet: {str(e)}', 500, False)


@app.route('/api/pcap/packet/<path:filepath>/<int:packet_index>', methods=['PUT'])
def modify_packet(filepath, packet_index):
    """
    Modify packet payload
    Request body: {
        'payload': 'hex_encoded_payload',
        'offset': 0  (optional, byte offset to start modification)
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'payload' not in data:
            return generate_response('Payload data required', 400, False)

        offset = data.get('offset', 0)
        result = pcap_handler.modify_packet_payload(
            filepath,
            packet_index,
            data['payload'],
            offset
        )

        if result:
            return generate_response(
                {'message': 'Packet modified successfully'},
                200,
                True
            )
        else:
            return generate_response('Failed to modify packet', 500, False)

    except Exception as e:
        return generate_response(f'Error modifying packet: {str(e)}', 500, False)


@app.route('/api/pcap/export/<path:filepath>', methods=['GET'])
def export_pcap(filepath):
    """Export modified PCAP file"""
    try:
        # Resolve + contain the path before serving it
        try:
            file_path = resolve_upload_path(filepath, app.config['UPLOAD_FOLDER'], must_exist=True)
        except FileNotFoundError:
            return generate_response('File not found', 404, False)
        except ValueError:
            return generate_response('Invalid file path', 400, False)

        filename = os.path.basename(file_path)
        return send_file(
            file_path,
            mimetype='application/octet-stream',
            as_attachment=True,
            download_name=filename
        )

    except Exception as e:
        return generate_response(f'Error exporting file: {str(e)}', 500, False)


@app.route('/api/pcap/statistics/<path:filepath>', methods=['GET'])
def get_statistics(filepath):
    """Get statistics about the PCAP file"""
    try:
        stats = pcap_handler.get_statistics(filepath)
        return generate_response(stats, 200, True)

    except Exception as e:
        return generate_response(f'Error retrieving statistics: {str(e)}', 500, False)


@app.route('/api/pcap/analyze/<path:filepath>/<int:packet_index>', methods=['GET'])
def analyze_packet(filepath, packet_index):
    """Analyze packet for HTTP Host or TLS SNI editing capabilities"""
    try:
        analysis = pcap_handler.analyze_packet_for_editing(filepath, packet_index)
        return generate_response(analysis, 200, True)

    except Exception as e:
        return generate_response(f'Error analyzing packet: {str(e)}', 500, False)


@app.route('/api/pcap/http-host/<path:filepath>/<int:packet_index>', methods=['PUT'])
def modify_http_host(filepath, packet_index):
    """
    Modify HTTP Host header
    Request body: {'host': 'new-hostname'}
    """
    try:
        data = request.get_json()
        
        if not data or 'host' not in data:
            return generate_response('Host value required', 400, False)

        result = pcap_handler.modify_http_host(filepath, packet_index, data['host'])

        if result['success']:
            result['modified_filepath'] = result.get('modified_filepath', '').replace('\\', '/')
            return generate_response(result, 200, True)
        else:
            return generate_response(result, 400, False)

    except Exception as e:
        return generate_response(f'Error modifying HTTP Host: {str(e)}', 500, False)


@app.route('/api/pcap/tls-sni/<path:filepath>/<int:packet_index>', methods=['PUT'])
def modify_tls_sni(filepath, packet_index):
    """
    Modify TLS SNI (Server Name Indication)
    Request body: {'sni': 'new-server-name'}
    """
    try:
        data = request.get_json()
        
        if not data or 'sni' not in data:
            return generate_response('SNI value required', 400, False)

        result = pcap_handler.modify_tls_sni(filepath, packet_index, data['sni'])

        if result['success']:
            result['modified_filepath'] = result.get('modified_filepath', '').replace('\\', '/')
            return generate_response(result, 200, True)
        else:
            return generate_response(result, 400, False)

    except Exception as e:
        return generate_response(f'Error modifying TLS SNI: {str(e)}', 500, False)


@app.route('/api/pcap/dns-query/<path:filepath>/<int:packet_index>', methods=['PUT'])
def modify_dns_query(filepath, packet_index):
    """
    Modify DNS query
    Request body: {'query': 'new.domain.com'}
    """
    try:
        data = request.get_json()
        
        if not data or 'query' not in data:
            return generate_response('Query value required', 400, False)

        result = pcap_handler.modify_dns_query(filepath, packet_index, data['query'])

        if result['success']:
            result['modified_filepath'] = result.get('modified_filepath', '').replace('\\', '/')
            return generate_response(result, 200, True)
        else:
            return generate_response(result, 400, False)

    except Exception as e:
        return generate_response(f'Error modifying DNS query: {str(e)}', 500, False)


@app.route('/api/pcap/ip/<path:filepath>/<int:packet_index>', methods=['PUT'])
def modify_ip(filepath, packet_index):
    """
    Modify IP addresses
    Request body: {'src_ip': '...', 'dst_ip': '...'}
    """
    try:
        data = request.get_json()
        
        if not data or (not data.get('src_ip') and not data.get('dst_ip')):
            return generate_response('At least one IP address required', 400, False)

        try:
            validate_network_fields({'src_ip': data.get('src_ip'), 'dst_ip': data.get('dst_ip')})
        except ValueError as e:
            return generate_response(str(e), 400, False)

        result = pcap_handler.modify_ip_addresses(
            filepath, packet_index, 
            data.get('src_ip'), 
            data.get('dst_ip')
        )

        if result['success']:
            result['modified_filepath'] = result.get('modified_filepath', '').replace('\\', '/')
            return generate_response(result, 200, True)
        else:
            return generate_response(result, 400, False)

    except Exception as e:
        return generate_response(f'Error modifying IP addresses: {str(e)}', 500, False)


@app.route('/api/pcap/port/<path:filepath>/<int:packet_index>', methods=['PUT'])
def modify_port(filepath, packet_index):
    """
    Modify ports
    Request body: {'src_port': 123, 'dst_port': 456}
    """
    try:
        data = request.get_json()
        
        if not data or (data.get('src_port') is None and data.get('dst_port') is None):
            return generate_response('At least one port required', 400, False)

        try:
            validate_network_fields({'src_port': data.get('src_port'), 'dst_port': data.get('dst_port')})
        except ValueError as e:
            return generate_response(str(e), 400, False)

        result = pcap_handler.modify_ports(
            filepath, packet_index,
            data.get('src_port'),
            data.get('dst_port')
        )

        if result['success']:
            result['modified_filepath'] = result.get('modified_filepath', '').replace('\\', '/')
            return generate_response(result, 200, True)
        else:
            return generate_response(result, 400, False)

    except Exception as e:
        return generate_response(f'Error modifying ports: {str(e)}', 500, False)


@app.route('/api/pcap/mac/<path:filepath>/<int:packet_index>', methods=['PUT'])
def modify_mac(filepath, packet_index):
    """
    Modify MAC addresses
    Request body: {'src_mac': '...', 'dst_mac': '...'}
    """
    try:
        data = request.get_json()
        
        if not data or (not data.get('src_mac') and not data.get('dst_mac')):
            return generate_response('At least one MAC address required', 400, False)

        try:
            validate_network_fields({'src_mac': data.get('src_mac'), 'dst_mac': data.get('dst_mac')})
        except ValueError as e:
            return generate_response(str(e), 400, False)

        result = pcap_handler.modify_mac_addresses(
            filepath, packet_index,
            data.get('src_mac'),
            data.get('dst_mac')
        )

        if result['success']:
            result['modified_filepath'] = result.get('modified_filepath', '').replace('\\', '/')
            return generate_response(result, 200, True)
        else:
            return generate_response(result, 400, False)

    except Exception as e:
        return generate_response(f'Error modifying MAC addresses: {str(e)}', 500, False)


@app.route('/api/pcap/vlan/<path:filepath>/<int:packet_index>', methods=['PUT'])
def modify_vlan(filepath, packet_index):
    """
    Modify VLAN ID
    Request body: {'vlan_id': 100}
    """
    try:
        data = request.get_json()
        
        if not data or 'vlan_id' not in data:
            return generate_response('VLAN ID required', 400, False)

        try:
            vlan_id = validate_vlan(data['vlan_id'])
        except ValueError as e:
            return generate_response(str(e), 400, False)

        result = pcap_handler.modify_vlan(filepath, packet_index, vlan_id)

        if result['success']:
            result['modified_filepath'] = result.get('modified_filepath', '').replace('\\', '/')
            return generate_response(result, 200, True)
        else:
            return generate_response(result, 400, False)

    except Exception as e:
        return generate_response(f'Error modifying VLAN: {str(e)}', 500, False)


@app.route('/api/pcap/vlan/<path:filepath>/<int:packet_index>', methods=['POST'])
def add_vlan(filepath, packet_index):
    """
    Add VLAN tag to packet
    Request body: {'vlan_id': 100, 'priority': 0}
    """
    try:
        data = request.get_json()
        
        if not data or 'vlan_id' not in data:
            return generate_response('VLAN ID required', 400, False)

        try:
            vlan_id = validate_vlan(data['vlan_id'])
            priority = int(data.get('priority', 0))
            if not (0 <= priority <= 7):
                raise ValueError(f'VLAN priority out of range (0-7): {priority}')
        except (ValueError, TypeError) as e:
            return generate_response(str(e), 400, False)

        result = pcap_handler.add_vlan(
            filepath, packet_index,
            vlan_id,
            priority
        )

        if result['success']:
            result['modified_filepath'] = result.get('modified_filepath', '').replace('\\', '/')
            return generate_response(result, 200, True)
        else:
            return generate_response(result, 400, False)

    except Exception as e:
        return generate_response(f'Error adding VLAN: {str(e)}', 500, False)


@app.route('/api/pcap/field-values/<path:filepath>', methods=['GET'])
def get_field_values(filepath):
    """
    Extract unique field values from an existing PCAP for seeding the generator.
    Returns { fields: { src_mac:[], dst_mac:[], src_ip:[], dst_ip:[],
                        src_port:[], dst_port:[], vlan_id:[] } }
    """
    try:
        result = pcap_handler.extract_field_values(filepath)
        if result['success']:
            return generate_response(result, 200, True)
        else:
            return generate_response(result.get('error', 'Extraction failed'), 400, False)
    except Exception as e:
        return generate_response(f'Error extracting field values: {str(e)}', 500, False)


@app.route('/api/pcap/bulk/<path:filepath>', methods=['POST'])
def bulk_modify_packets(filepath):
    """
    Bulk-modify selected packets.
    Request body: {
        'packet_indices': [0, 1, 5],  // omit or null = all packets
        'fields': { 'src_ip': '10.0.0.1', 'dst_mac': 'aa:bb:cc:dd:ee:ff', ... },
        'incremental': {              // optional
            'enabled': true,
            'step': 1,
            'fields': ['src_ip', 'dst_ip', 'src_port', 'dst_port']
        }
    }
    """
    try:
        data = request.get_json()
        if not data or 'fields' not in data:
            return generate_response('fields dict is required', 400, False)

        fields = data.get('fields', {})
        packet_indices = data.get('packet_indices', None)  # None = all
        incremental = data.get('incremental', None)
        keep_unselected = data.get('keep_unselected', True)

        try:
            validate_network_fields(fields)
        except ValueError as e:
            return generate_response(str(e), 400, False)

        result = pcap_handler.bulk_modify_packets(filepath, packet_indices, fields, incremental, keep_unselected)
        if result['success']:
            result['modified_filepath'] = result.get('modified_filepath', '').replace('\\', '/')
            return generate_response(result, 200, True)
        else:
            return generate_response(result, 400, False)

    except Exception as e:
        return generate_response(f'Error in bulk modify: {str(e)}', 500, False)


@app.route('/api/pcap/replicate/<path:filepath>', methods=['POST'])
def replicate_packets(filepath):
    """
    Replicate selected packets N times.
    Request body: { 'packet_indices': [0, 1, 2], 'count': 3 }
    Copies inserted after the last selected packet, originals preserved.
    """
    try:
        data = request.get_json()
        if not data or 'packet_indices' not in data or 'count' not in data:
            return generate_response('packet_indices and count are required', 400, False)

        count = int(data['count'])
        if count < 1 or count > 10000:
            return generate_response('count must be between 1 and 10000', 400, False)

        result = pcap_handler.replicate_packets(filepath, data['packet_indices'], count)
        if result['success']:
            result['modified_filepath'] = result.get('modified_filepath', '').replace('\\', '/')
            return generate_response(result, 200, True)
        else:
            return generate_response(result, 400, False)
    except Exception as e:
        return generate_response(f'Error replicating packets: {str(e)}', 500, False)


@app.route('/api/pcap/extract/<path:filepath>', methods=['POST'])
def extract_packets(filepath):
    """
    Extract selected packets into a new PCAP file (source left unchanged).
    Request body: { 'packet_indices': [0, 2, 5] }
    """
    try:
        data = request.get_json()
        if not data or 'packet_indices' not in data:
            return generate_response('packet_indices is required', 400, False)

        indices = data['packet_indices']
        if not isinstance(indices, list) or len(indices) == 0:
            return generate_response('packet_indices must be a non-empty list', 400, False)

        result = pcap_handler.extract_packets(filepath, indices)
        if result['success']:
            result['filepath'] = result.get('filepath', '').replace('\\', '/')
            return generate_response(result, 200, True)
        else:
            return generate_response(result, 400, False)
    except Exception as e:
        return generate_response(f'Error extracting packets: {str(e)}', 500, False)


@app.route('/api/pcap/packet/<path:filepath>/<int:packet_index>', methods=['DELETE'])
def delete_packet(filepath, packet_index):
    """Delete a specific packet from the PCAP file."""
    try:
        result = pcap_handler.delete_packet(filepath, packet_index)
        if result['success']:
            result['modified_filepath'] = result.get('modified_filepath', '').replace('\\', '/')
            return generate_response(result, 200, True)
        else:
            return generate_response(result, 400, False)
    except Exception as e:
        return generate_response(f'Error deleting packet: {str(e)}', 500, False)


@app.route('/api/pcap/packet/<path:filepath>/<int:packet_index>/duplicate', methods=['POST'])
def duplicate_packet(filepath, packet_index):
    """Duplicate a packet (insert copy after original)."""
    try:
        result = pcap_handler.duplicate_packet(filepath, packet_index)
        if result['success']:
            result['modified_filepath'] = result.get('modified_filepath', '').replace('\\', '/')
            return generate_response(result, 200, True)
        else:
            return generate_response(result, 400, False)
    except Exception as e:
        return generate_response(f'Error duplicating packet: {str(e)}', 500, False)


@app.route('/api/pcap/packet/<path:filepath>/<int:packet_index>/move', methods=['PUT'])
def move_packet(filepath, packet_index):
    """
    Move a packet.
    Request body: { 'direction': 'up' | 'down' | 'top' | 'bottom' }
    """
    try:
        data = request.get_json()
        if not data or 'direction' not in data:
            return generate_response('direction is required', 400, False)
        result = pcap_handler.move_packet(filepath, packet_index, data['direction'])
        if result['success']:
            result['modified_filepath'] = result.get('modified_filepath', '').replace('\\', '/')
            return generate_response(result, 200, True)
        else:
            return generate_response(result, 400, False)
    except Exception as e:
        return generate_response(f'Error moving packet: {str(e)}', 500, False)


@app.route('/api/pcap/generate', methods=['POST'])
def generate_pcap():
    """
    Generate a new PCAP file with specified protocol
    Expected JSON: {
        "protocol": "tcp|http|udp|dns_udp|dns_tcp|tls",
        "packet_count": 10,
        "vlan_id": 100 (optional),
        "options": {
            "src_mac": "00:0c:29:63:c0:fb",
            "dst_mac": "00:0c:29:63:c0:fa",
            "src_ip": "192.168.1.100",
            "dst_ip": "192.168.1.200",
            "src_port": 12345,
            "dst_port": 80,
            "http_host": "example.com",
            "dns_query": "example.com",
            "tls_sni": "example.com"
        }
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return generate_response('No data provided', 400, False)
        
        protocol = data.get('protocol')
        packet_count = data.get('packet_count', 10)
        vlan_id = data.get('vlan_id')
        options = data.get('options', {})
        
        if not protocol:
            return generate_response('Protocol is required', 400, False)

        try:
            packet_count = int(packet_count)
        except (TypeError, ValueError):
            return generate_response('packet_count must be an integer', 400, False)

        if packet_count < 1 or packet_count > 1000:
            return generate_response('Packet count must be between 1 and 1000', 400, False)

        try:
            if vlan_id is not None:
                vlan_id = validate_vlan(vlan_id)
            validate_network_fields(options)
        except ValueError as e:
            return generate_response(str(e), 400, False)

        # Generate PCAP
        result = pcap_handler.generate_pcap(protocol, packet_count, vlan_id, options)
        
        if result['success']:
            return jsonify({
                'success': True,
                'filepath': result['filepath'].replace('\\', '/'),
                'packet_count': result['packet_count'],
                'protocol': result['protocol'],
                'vlan_id': result.get('vlan_id'),
                'message': f'Generated {result["packet_count"]} {protocol} packets'
            })
        else:
            return generate_response(result['error'], 400, False)
    
    except Exception as e:
        return generate_response(f'Error generating PCAP: {str(e)}', 500, False)


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return generate_response('Endpoint not found', 404, False)


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return generate_response('Internal server error', 500, False)


@app.route('/api/pcap/merge', methods=['POST'])
def merge_pcaps():
    """Merge two or more PCAP/PCAPNG files into a single PCAP"""
    try:
        files = request.files.getlist('files')

        if not files or len(files) < 2:
            return generate_response('At least two PCAP files are required', 400, False)

        saved_paths = []
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        for idx, file in enumerate(files, start=1):
            if file.filename == '':
                return generate_response('One of the files has no name', 400, False)

            if not allowed_file(file.filename, ALLOWED_EXTENSIONS):
                return generate_response('Invalid file type. Only .pcap and .pcapng allowed', 400, False)

            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], f"{timestamp}_{idx}_{filename}")
            file.save(filepath)
            saved_paths.append(filepath)

        output_name = request.form.get('output_name')
        result = pcap_handler.merge_pcaps(saved_paths, output_name)

        if result['success']:
            return jsonify({
                'success': True,
                'filepath': result['filepath'].replace('\\', '/'),
                'packet_count': result['packet_count'],
                'source_files': result['source_files'],
                'message': f"Merged {len(saved_paths)} files into {os.path.basename(result['filepath'])}"
            })
        else:
            return generate_response(result['error'], 400, False)

    except Exception as e:
        return generate_response(f'Error merging PCAP files: {str(e)}', 500, False)


# ---------------------------------------------------------------------------
# File Management Endpoints
# ---------------------------------------------------------------------------

@app.route('/api/files', methods=['GET'])
def list_files():
    """List all files in the uploads folder with metadata."""
    try:
        files = []
        for filename in os.listdir(UPLOAD_FOLDER):
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            if os.path.isfile(filepath):
                stat = os.stat(filepath)
                files.append({
                    'name': filename,
                    'size': stat.st_size,
                    'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    'extension': os.path.splitext(filename)[1].lower().lstrip('.')
                })
        files.sort(key=lambda x: x['modified'], reverse=True)
        return jsonify({'success': True, 'files': files, 'count': len(files)})
    except Exception as e:
        return generate_response(f'Error listing files: {str(e)}', 500, False)


@app.route('/api/files/<filename>', methods=['DELETE'])
def delete_upload_file(filename):
    """Delete a file from the uploads folder."""
    try:
        filepath = os.path.join(UPLOAD_FOLDER, secure_filename(filename))
        if not os.path.exists(filepath):
            return generate_response('File not found', 404, False)
        os.remove(filepath)
        return jsonify({'success': True, 'message': f'File {filename} deleted'})
    except Exception as e:
        return generate_response(f'Error deleting file: {str(e)}', 500, False)


@app.route('/api/files/<filename>/rename', methods=['PUT'])
def rename_upload_file(filename):
    """
    Rename a file in uploads.
    Request body: { 'new_name': 'new_filename.pcap' }
    """
    try:
        data = request.get_json()
        if not data or 'new_name' not in data:
            return generate_response('new_name is required', 400, False)
        old_path = os.path.join(UPLOAD_FOLDER, secure_filename(filename))
        new_name = secure_filename(data['new_name'])
        new_path = os.path.join(UPLOAD_FOLDER, new_name)
        if not os.path.exists(old_path):
            return generate_response('File not found', 404, False)
        if os.path.exists(new_path):
            return generate_response('A file with that name already exists', 400, False)
        os.rename(old_path, new_path)
        return jsonify({'success': True, 'new_name': new_name})
    except Exception as e:
        return generate_response(f'Error renaming file: {str(e)}', 500, False)


@app.route('/api/hex/upload', methods=['POST'])
def upload_hex_file():
    """Upload any file for hex viewing"""
    try:
        if 'file' not in request.files:
            return generate_response('No file provided', 400, False)

        file = request.files['file']
        
        if file.filename == '':
            return generate_response('No file selected', 400, False)

        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], timestamp + filename)

        # Save file
        file.save(filepath)

        # Read file as hex
        with open(filepath, 'rb') as f:
            file_bytes = f.read()
            hex_data = file_bytes.hex()
        
        file_size = len(file_bytes)
        
        # Try to decode as text for human-readable view
        text_content = None
        file_type = 'binary'
        encoding_used = None
        
        # Try different encodings
        for encoding in ['utf-8', 'ascii', 'latin-1', 'utf-16', 'utf-32']:
            try:
                decoded = file_bytes.decode(encoding)
                # Check if it's mostly printable characters
                printable_ratio = sum(c.isprintable() or c in '\n\r\t' for c in decoded) / len(decoded) if decoded else 0
                if printable_ratio > 0.7:  # At least 70% printable
                    text_content = decoded
                    encoding_used = encoding
                    file_type = 'text'
                    
                    # Detect specific formats
                    if decoded.strip().startswith('{') or decoded.strip().startswith('['):
                        try:
                            json.loads(decoded)
                            file_type = 'json'
                        except:
                            pass
                    elif decoded.strip().startswith('<'):
                        file_type = 'xml'
                    
                    break
            except (UnicodeDecodeError, UnicodeError):
                continue
        
        response_data = {
            'success': True,
            'filename': filename,
            'filepath': filepath,
            'size': file_size,
            'hex': hex_data,
            'file_type': file_type,
            'encoding': encoding_used
        }
        
        if text_content is not None:
            response_data['text'] = text_content
        
        return jsonify(response_data)

    except Exception as e:
        return generate_response(f'Error uploading file: {str(e)}', 500, False)


# =============================================================================
# PDF Editor Routes
# =============================================================================

@app.route('/api/pdf/upload', methods=['POST'])
def upload_pdf():
    """Upload a PDF file and return basic metadata."""
    if 'file' not in request.files:
        return generate_response('No file provided', 400, False)
    f = request.files['file']
    if not f.filename:
        return generate_response('No file selected', 400, False)
    if not f.filename.lower().endswith('.pdf'):
        return generate_response('Only PDF files are supported', 400, False)
    filename = secure_filename(f.filename)
    save_path = os.path.join(UPLOAD_FOLDER, filename)
    f.save(save_path)
    try:
        info = pdf_handler.get_info(filename)
        info['filepath'] = filename
        return generate_response(info, 200, True)
    except Exception as e:
        return generate_response(str(e), 500, False)


@app.route('/api/pdf/<path:filepath>/info', methods=['GET'])
def get_pdf_info(filepath):
    try:
        result = pdf_handler.get_info(filepath)
        return generate_response(result, 200, True) if result['success'] \
            else generate_response(result.get('error', 'Failed'), 400, False)
    except Exception as e:
        return generate_response(str(e), 500, False)


@app.route('/api/pdf/<path:filepath>/page/<int:page_num>', methods=['GET'])
def render_pdf_page(filepath, page_num):
    try:
        scale = float(request.args.get('scale', 1.5))
        result = pdf_handler.render_page(filepath, page_num, scale)
        return generate_response(result, 200, True) if result['success'] \
            else generate_response(result.get('error', 'Failed'), 400, False)
    except Exception as e:
        return generate_response(str(e), 500, False)


@app.route('/api/pdf/<path:filepath>/text/<int:page_num>', methods=['GET'])
def get_pdf_text(filepath, page_num):
    try:
        result = pdf_handler.get_text_blocks(filepath, page_num)
        return generate_response(result, 200, True) if result['success'] \
            else generate_response(result.get('error', 'Failed'), 400, False)
    except Exception as e:
        return generate_response(str(e), 500, False)


@app.route('/api/pdf/<path:filepath>/save', methods=['POST'])
def save_pdf(filepath):
    """Apply text edits and save as a new PDF file."""
    try:
        data = request.get_json() or {}
        edits = data.get('edits', [])
        deleted_pages = data.get('deleted_pages', [])
        metadata = data.get('metadata', None)
        watermark = data.get('watermark', None)
        output_name = data.get('output_name', None)
        result = pdf_handler.apply_edits(filepath, edits, output_name, deleted_pages, metadata, watermark)
        if result['success']:
            result['output_path'] = result.get('output_path', '').replace('\\', '/')
            return generate_response(result, 200, True)
        return generate_response(result.get('error', 'Save failed'), 400, False)
    except Exception as e:
        return generate_response(str(e), 500, False)

@app.route('/api/pdf/<path:filepath>/append', methods=['POST'])
def append_pdf(filepath):
    """Append a second PDF to the current working PDF."""
    try:
        if 'file' not in request.files:
            return generate_response('No file part', 400, False)
            
        file = request.files['file']
        if file.filename == '' or not allowed_file(file.filename, {'pdf'}):
            return generate_response('Invalid file', 400, False)

        # Save the appended file temporarily
        append_filename = secure_filename(file.filename)
        append_filepath = os.path.join(app.config['UPLOAD_FOLDER'], 'append_' + append_filename)
        file.save(append_filepath)
        
        # Append it
        result = pdf_handler.append_pdf(filepath, append_filepath)
        
        # Cleanup temp file
        if os.path.exists(append_filepath):
            os.remove(append_filepath)
            
        if result['success']:
            return generate_response(result, 200, True)
        return generate_response(result.get('error', 'Append failed'), 400, False)
    except Exception as e:
        return generate_response(str(e), 500, False)


@app.route('/api/pdf/<path:filepath>/ocr/<int:page_num>', methods=['POST'])
def ocr_pdf_page(filepath, page_num):
    """Run Tesseract OCR on a scanned PDF page and return text spans."""
    try:
        data = request.get_json() or {}
        lang = data.get('lang', 'eng')
        result = pdf_handler.ocr_page(filepath, page_num, lang=lang)
        if result['success']:
            return generate_response(result, 200, True)
        return generate_response(result.get('error', 'OCR failed'), 400, False)
    except Exception as e:
        return generate_response(str(e), 500, False)


@app.route('/api/pdf/download/<path:filepath>', methods=['GET'])
def download_pdf(filepath):
    try:
        resolved = pdf_handler._resolve(filepath)
        return send_file(resolved, as_attachment=True,
                         download_name=os.path.basename(resolved))
    except Exception as e:
        return generate_response(str(e), 404, False)


# =========================================================================== #
#  Receipt Editor API
# =========================================================================== #

@app.route('/api/receipt/upload', methods=['POST'])
def receipt_upload():
    """Upload JPG/PNG/PDF scan, run OCR, return fields + spans."""
    if not _RECEIPT_AVAILABLE:
        return generate_response('Receipt editor requires opencv-python (cv2), which is not installed on this system', 503, False)
    try:
        if 'file' not in request.files:
            return generate_response('No file provided', 400, False)
        file = request.files['file']
        if not file.filename:
            return generate_response('Empty filename', 400, False)
        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in ('.jpg', '.jpeg', '.png', '.pdf'):
            return generate_response('Unsupported file type. Use JPG, PNG or PDF.', 400, False)
        lang = request.form.get('lang', 'eng')
        result = receipt_handler.upload_and_scan(file, lang=lang)
        return generate_response(result, 200, True)
    except Exception as e:
        return generate_response(str(e), 500, False)


@app.route('/api/receipt/process', methods=['POST'])
def receipt_process():
    """Apply edits to receipt image, return edited image + result filename."""
    if not _RECEIPT_AVAILABLE:
        return generate_response('Receipt editor requires opencv-python (cv2), which is not installed on this system', 503, False)
    try:
        data = request.get_json()
        if not data:
            return generate_response('No JSON body', 400, False)
        filepath      = data.get('filepath')
        edits         = data.get('edits', [])
        output_format = data.get('output_format', 'pdf')
        appearance    = data.get('appearance', {})
        if not filepath:
            return generate_response('filepath required', 400, False)
        result = receipt_handler.process_edits(filepath, edits, output_format,
                                               appearance_settings=appearance)
        return generate_response(result, 200, True)
    except FileNotFoundError as e:
        return generate_response(str(e), 404, False)
    except Exception as e:
        return generate_response(str(e), 500, False)


@app.route('/api/receipt/download/<path:filename>', methods=['GET'])
def receipt_download(filename):
    """Download the generated receipt PDF/PNG."""
    if not _RECEIPT_AVAILABLE:
        return generate_response('Receipt editor requires opencv-python (cv2), which is not installed on this system', 503, False)
    try:
        path = os.path.abspath(os.path.join(UPLOAD_FOLDER, os.path.basename(filename)))
        if not os.path.exists(path):
            return generate_response('File not found', 404, False)
        return send_file(path, as_attachment=True,
                         download_name=os.path.basename(path))
    except Exception as e:
        return generate_response(str(e), 500, False)


if __name__ == '__main__':
    # app.run(debug=True, host='0.0.0.0', port=5000)
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() in ('true', '1', 't')
    app.run(debug=debug_mode, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

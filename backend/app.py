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
from utils import generate_response, allowed_file

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

# Initialize PCAP handler
pcap_handler = PCAPHandler(UPLOAD_FOLDER)


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
                'filepath': filepath,
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
        # Read packets
        packets = pcap_handler.read_pcap(filepath)
        
        # Resolve path for size lookup
        if os.path.isabs(filepath):
            file_path = filepath
        elif filepath.startswith(app.config['UPLOAD_FOLDER']):
            file_path = filepath
        else:
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filepath)

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
        # Resolve path similar to get_pcap_file
        if os.path.isabs(filepath):
            file_path = filepath
        elif filepath.startswith(app.config['UPLOAD_FOLDER']):
            file_path = filepath
        else:
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filepath)

        if not os.path.exists(file_path):
            return generate_response('File not found', 404, False)

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

        result = pcap_handler.modify_ip_addresses(
            filepath, packet_index, 
            data.get('src_ip'), 
            data.get('dst_ip')
        )

        if result['success']:
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
        
        if not data or (not data.get('src_port') and not data.get('dst_port')):
            return generate_response('At least one port required', 400, False)

        result = pcap_handler.modify_ports(
            filepath, packet_index,
            data.get('src_port'),
            data.get('dst_port')
        )

        if result['success']:
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

        result = pcap_handler.modify_mac_addresses(
            filepath, packet_index,
            data.get('src_mac'),
            data.get('dst_mac')
        )

        if result['success']:
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

        result = pcap_handler.modify_vlan(filepath, packet_index, data['vlan_id'])

        if result['success']:
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

        result = pcap_handler.add_vlan(
            filepath, packet_index,
            data['vlan_id'],
            data.get('priority', 0)
        )

        if result['success']:
            return generate_response(result, 200, True)
        else:
            return generate_response(result, 400, False)

    except Exception as e:
        return generate_response(f'Error adding VLAN: {str(e)}', 500, False)


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
        
        if packet_count < 1 or packet_count > 1000:
            return generate_response('Packet count must be between 1 and 1000', 400, False)
        
        # Generate PCAP
        result = pcap_handler.generate_pcap(protocol, packet_count, vlan_id, options)
        
        if result['success']:
            return jsonify({
                'success': True,
                'filepath': result['filepath'],
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
                'filepath': result['filepath'],
                'packet_count': result['packet_count'],
                'source_files': result['source_files'],
                'message': f"Merged {len(saved_paths)} files into {os.path.basename(result['filepath'])}"
            })
        else:
            return generate_response(result['error'], 400, False)

    except Exception as e:
        return generate_response(f'Error merging PCAP files: {str(e)}', 500, False)


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


if __name__ == '__main__':
    # app.run(debug=True, host='0.0.0.0', port=5000)
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() in ('true', '1', 't')
    app.run(debug=debug_mode, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

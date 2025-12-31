"""
Utility functions for PCAP Editor API
"""

from flask import jsonify


def generate_response(data, status_code, success):
    """
    Generate standardized JSON response
    """
    response = {
        'success': success,
        'status_code': status_code,
        'data': data if isinstance(data, dict) else {'message': data}
    }
    return jsonify(response), status_code


def allowed_file(filename, allowed_extensions):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

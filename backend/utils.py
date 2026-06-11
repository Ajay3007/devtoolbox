"""
Utility functions for PCAP Editor API
"""

import os

from flask import jsonify


def resolve_upload_path(filepath, upload_folder, must_exist=False):
    """
    Resolve a user-supplied filepath to an absolute path that is guaranteed to
    live inside ``upload_folder``. Rejects absolute paths and ``../`` traversal.

    Accepts either a bare name ("foo.pcap") or an upload-relative path
    ("uploads/foo.pcap", "<session>/foo.pcap"). A leading slash and an optional
    leading "<upload_folder_name>/" segment are stripped before resolution so
    callers can pass back the same path the API returned.

    Raises ValueError if the path escapes the upload directory, and
    FileNotFoundError if ``must_exist`` is set and the target does not exist.
    """
    upload_root = os.path.realpath(upload_folder)
    raw = str(filepath).replace('\\', '/').strip()

    # If an absolute path that already lives inside the upload root is passed
    # back in (handlers re-pass resolved paths), accept it unchanged. This makes
    # the resolver idempotent.
    already = os.path.realpath(raw)
    if already == upload_root or already.startswith(upload_root + os.sep):
        full = already
    else:
        rel = raw.lstrip('/')
        prefix = os.path.basename(upload_root) + '/'
        if rel.startswith(prefix):
            rel = rel[len(prefix):]
        full = os.path.realpath(os.path.join(upload_root, rel))
        if full != upload_root and not full.startswith(upload_root + os.sep):
            raise ValueError(f'Path escapes upload directory: {filepath}')

    if must_exist and not os.path.exists(full):
        raise FileNotFoundError(f'File not found: {filepath}')
    return full


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

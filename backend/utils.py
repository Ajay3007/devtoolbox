"""
Utility functions for PCAP Editor API
"""

import os
import re
import ipaddress

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


# ---------------------------------------------------------------------------
# Network value validation
#
# User-supplied IPs/MACs/ports/VLANs are passed straight into Scapy, which
# silently accepts garbage and can produce a corrupt capture. Validate at the
# API boundary and raise ValueError (mapped to HTTP 400) on bad input.
# ---------------------------------------------------------------------------

_MAC_RE = re.compile(r'^([0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}$')

# Network fields that have a dedicated validator. Used by validate_network_fields.
_NETWORK_VALIDATORS = {}


def validate_ip(value, field='ip'):
    """Raise ValueError unless value is a valid IPv4/IPv6 address string."""
    try:
        ipaddress.ip_address(value)
    except (ValueError, TypeError):
        raise ValueError(f'Invalid IP address for {field}: {value!r}')
    return value


def validate_mac(value, field='mac'):
    """Raise ValueError unless value is a valid colon/dash MAC address."""
    if not isinstance(value, str) or not _MAC_RE.match(value):
        raise ValueError(f'Invalid MAC address for {field}: {value!r}')
    return value


def validate_port(value, field='port'):
    """Return int port in 0-65535 or raise ValueError."""
    try:
        port = int(value)
    except (TypeError, ValueError):
        raise ValueError(f'Invalid port for {field}: {value!r}')
    if not (0 <= port <= 65535):
        raise ValueError(f'Port out of range for {field} (0-65535): {port}')
    return port


def validate_vlan(value, field='vlan_id'):
    """Return int VLAN id in 0-4094 or raise ValueError."""
    try:
        vlan = int(value)
    except (TypeError, ValueError):
        raise ValueError(f'Invalid VLAN id for {field}: {value!r}')
    if not (0 <= vlan <= 4094):
        raise ValueError(f'VLAN id out of range for {field} (0-4094): {vlan}')
    return vlan


_NETWORK_VALIDATORS.update({
    'src_ip': validate_ip, 'dst_ip': validate_ip,
    'src_mac': validate_mac, 'dst_mac': validate_mac,
    'src_port': validate_port, 'dst_port': validate_port,
    'vlan_id': validate_vlan,
})


def validate_network_fields(fields):
    """Validate any recognized network keys present (and not None) in `fields`.

    Raises ValueError on the first invalid value. Unknown keys are ignored so
    callers can pass a superset dict (e.g. the bulk-edit fields payload).
    """
    if not isinstance(fields, dict):
        return
    for key, validator in _NETWORK_VALIDATORS.items():
        # None / '' mean "leave unchanged" in the modify + bulk flows; skip them.
        if fields.get(key) not in (None, ''):
            validator(fields[key], field=key)

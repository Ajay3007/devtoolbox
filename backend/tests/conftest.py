"""
Shared pytest fixtures.

Tests run against a temporary upload directory so they never touch the real
backend/uploads folder. The app module's handler singletons are re-pointed at
the temp dir for the duration of each test.
"""
import os
import sys

import pytest

# Make the backend package importable regardless of pytest's rootdir.
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)


@pytest.fixture
def upload_dir(tmp_path):
    d = tmp_path / "uploads"
    d.mkdir()
    return str(d)


@pytest.fixture
def handler(upload_dir):
    """A PCAPHandler bound to an isolated temp upload dir."""
    from pcap_handler import PCAPHandler
    return PCAPHandler(upload_dir)


@pytest.fixture
def client(upload_dir):
    """Flask test client with all handlers pointed at the temp upload dir."""
    import app as app_module

    app_module.UPLOAD_FOLDER = upload_dir
    app_module.app.config["UPLOAD_FOLDER"] = upload_dir
    app_module.app.config["TESTING"] = True
    app_module.pcap_handler.upload_folder = upload_dir
    app_module.pcap_handler._cache.clear()
    app_module.pdf_handler.upload_folder = upload_dir
    if getattr(app_module, "receipt_handler", None):
        app_module.receipt_handler.upload_folder = upload_dir
    return app_module.app.test_client()


def find_packet_index(handler, filepath, predicate):
    """Return the first packet index whose detail dict satisfies predicate."""
    packets = handler.read_pcap(filepath)
    for p in packets:
        if predicate(p):
            return p["index"]
    return None

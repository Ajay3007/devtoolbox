"""Path containment tests for resolve_upload_path()."""
import os

import pytest

from utils import resolve_upload_path


def test_bare_name_resolves_into_upload_dir(upload_dir):
    open(os.path.join(upload_dir, "a.pcap"), "wb").close()
    resolved = resolve_upload_path("a.pcap", upload_dir, must_exist=True)
    assert resolved == os.path.realpath(os.path.join(upload_dir, "a.pcap"))


def test_upload_prefixed_path_is_accepted(upload_dir):
    open(os.path.join(upload_dir, "a.pcap"), "wb").close()
    # The API hands paths back as "<upload_dir_name>/a.pcap"
    name = os.path.basename(os.path.realpath(upload_dir))
    resolved = resolve_upload_path(f"{name}/a.pcap", upload_dir, must_exist=True)
    assert resolved.endswith("a.pcap")


def test_resolver_is_idempotent(upload_dir):
    open(os.path.join(upload_dir, "a.pcap"), "wb").close()
    once = resolve_upload_path("a.pcap", upload_dir)
    twice = resolve_upload_path(once, upload_dir)
    assert once == twice


@pytest.mark.parametrize("bad", [
    "../../etc/passwd",
    "..\\..\\windows\\win.ini",
    "C:\\Windows\\win.ini",
    "/etc/shadow" if os.name != "nt" else "\\\\server\\share\\x",
    "uploads/../../../secret",
])
def test_traversal_is_blocked(upload_dir, bad):
    with pytest.raises((ValueError, FileNotFoundError)):
        resolve_upload_path(bad, upload_dir, must_exist=True)


def test_missing_file_raises_when_must_exist(upload_dir):
    with pytest.raises(FileNotFoundError):
        resolve_upload_path("nope.pcap", upload_dir, must_exist=True)

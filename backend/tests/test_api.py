"""
API-level tests via the Flask test client.

NOTE: a few of these assert the current response envelope. When the envelope
is standardized, update the shape assertions here (helper _data below
centralizes that).
"""
import io


def _generate(client, protocol="tcp", count=1, **opts):
    body = {"protocol": protocol, "packet_count": count}
    if opts:
        body["options"] = opts
    r = client.post("/api/pcap/generate", json=body)
    assert r.status_code == 200, r.get_data(as_text=True)
    fp = r.get_json()["filepath"]
    return fp.split("/")[-1]  # basename; resolver accepts bare names


def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.get_json()["status"] == "healthy"


def test_generate_then_list_packets(client):
    name = _generate(client, "tcp", 1)
    r = client.get(f"/api/pcap/packets/{name}")
    assert r.status_code == 200
    data = r.get_json()["data"]
    assert data["total"] > 0
    assert len(data["packets"]) == data["total"]


def test_generate_rejects_bad_count(client):
    r = client.post("/api/pcap/generate", json={"protocol": "tcp", "packet_count": 99999})
    assert r.status_code == 400


def test_generate_rejects_bad_ip_option(client):
    r = client.post("/api/pcap/generate",
                    json={"protocol": "tcp", "packet_count": 1, "options": {"src_ip": "not-an-ip"}})
    assert r.status_code == 400


def test_upload_round_trip(client, upload_dir, handler):
    # Build a real pcap on disk via the handler, then upload its bytes.
    src = handler.generate_pcap("tcp", 1, None, {})["filepath"]
    with open(src, "rb") as f:
        blob = f.read()
    data = {"file": (io.BytesIO(blob), "capture.pcap")}
    r = client.post("/api/pcap/upload", data=data, content_type="multipart/form-data")
    assert r.status_code == 200
    payload = r.get_json()["data"]
    assert payload["packet_count"] > 0


def test_modify_ip_valid(client):
    name = _generate(client, "tcp", 1)
    r = client.put(f"/api/pcap/ip/{name}/0", json={"src_ip": "9.9.9.9"})
    assert r.status_code == 200
    assert r.get_json()["data"]["success"] is True


def test_modify_ip_invalid_returns_400(client):
    name = _generate(client, "tcp", 1)
    r = client.put(f"/api/pcap/ip/{name}/0", json={"src_ip": "999.1.1.1"})
    assert r.status_code == 400


def test_modify_port_invalid_returns_400(client):
    name = _generate(client, "tcp", 1)
    r = client.put(f"/api/pcap/port/{name}/0", json={"src_port": 70000})
    assert r.status_code == 400


def test_export_traversal_is_blocked(client):
    # Encoded traversal must not return file contents.
    for attempt in ["%2e%2e%2f%2e%2e%2fetc%2fpasswd", "..%2f..%2fwin.ini"]:
        r = client.get(f"/api/pcap/export/{attempt}")
        assert r.status_code in (400, 404), f"{attempt} -> {r.status_code}"


def test_export_valid_file(client):
    name = _generate(client, "tcp", 1)
    r = client.get(f"/api/pcap/export/{name}")
    assert r.status_code == 200
    assert len(r.get_data()) > 0

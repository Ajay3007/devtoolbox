"""
PCAPHandler behavior tests.

These exercise the public handler API (generate, read, modify, bulk,
structural ops) so they remain valid across the planned internal refactors
(TLS-via-Scapy, module split).
"""
import pytest

from conftest import find_packet_index


# --------------------------------------------------------------------------- #
#  Generation
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("protocol", ["tcp", "http", "tls", "udp", "dns_udp", "dns_tcp", "icmp", "arp"])
def test_generate_each_protocol(handler, protocol):
    res = handler.generate_pcap(protocol, 2, None, {})
    assert res["success"], res
    assert res["packet_count"] > 0
    # The generated file is readable and reports the same count.
    packets = handler.read_pcap(res["filepath"])
    assert len(packets) == res["packet_count"]


def test_generate_unknown_protocol_fails(handler):
    res = handler.generate_pcap("flooberic", 1, None, {})
    assert res["success"] is False


def test_generate_with_vlan_tags_packets(handler):
    res = handler.generate_pcap("tcp", 1, 100, {})
    assert res["success"]
    # Every generated packet should carry the VLAN tag.
    from scapy.all import rdpcap, Dot1Q
    for pkt in rdpcap(res["filepath"]):
        assert pkt.haslayer(Dot1Q)
        assert pkt[Dot1Q].vlan == 100


def test_generate_fixed_packet_size(handler):
    res = handler.generate_pcap("udp", 1, None, {"packet_size": 200})
    assert res["success"]
    from scapy.all import rdpcap
    sizes = [len(p) for p in rdpcap(res["filepath"])]
    assert any(s == 200 for s in sizes)


# --------------------------------------------------------------------------- #
#  TLS SNI round-trip
# --------------------------------------------------------------------------- #
def test_tls_sni_extract_and_modify(handler):
    res = handler.generate_pcap("tls", 1, None, {"tls_sni": "example.com"})
    fp = res["filepath"]
    idx = find_packet_index(handler, fp, lambda p: p.get("packet_type") == "TLS")
    assert idx is not None
    assert handler.get_tls_sni(fp, idx) == "example.com"

    out = handler.modify_tls_sni(fp, idx, "changed.example.org")
    assert out["success"], out
    mod = out["modified_filepath"]
    new_idx = find_packet_index(handler, mod, lambda p: p.get("packet_type") == "TLS")
    assert handler.get_tls_sni(mod, new_idx) == "changed.example.org"


# --------------------------------------------------------------------------- #
#  DNS query round-trip
# --------------------------------------------------------------------------- #
def test_dns_query_extract_and_modify(handler):
    res = handler.generate_pcap("dns_udp", 1, None, {"dns_query": "example.com"})
    fp = res["filepath"]
    idx = find_packet_index(handler, fp, lambda p: p.get("packet_type") == "DNS")
    assert idx is not None
    assert handler.get_dns_query(fp, idx) == "example.com"

    out = handler.modify_dns_query(fp, idx, "changed.org")
    assert out["success"], out


# --------------------------------------------------------------------------- #
#  HTTP host
# --------------------------------------------------------------------------- #
def test_http_host_extract_and_modify(handler):
    res = handler.generate_pcap("http", 1, None, {"http_host": "example.com"})
    fp = res["filepath"]
    idx = find_packet_index(handler, fp, lambda p: p.get("packet_type") == "HTTP")
    assert idx is not None
    assert handler.get_http_host(fp, idx) == "example.com"

    out = handler.modify_http_host(fp, idx, "new-host.test")
    assert out["success"], out
    mod = out["modified_filepath"]
    new_idx = find_packet_index(handler, mod, lambda p: p.get("packet_type") == "HTTP")
    assert handler.get_http_host(mod, new_idx) == "new-host.test"


# --------------------------------------------------------------------------- #
#  Field modifications
# --------------------------------------------------------------------------- #
def test_modify_ip_addresses(handler):
    fp = handler.generate_pcap("tcp", 1, None, {})["filepath"]
    out = handler.modify_ip_addresses(fp, 0, "1.2.3.4", "5.6.7.8")
    assert out["success"]
    from scapy.all import rdpcap, IP
    pkt = rdpcap(out["modified_filepath"])[0]
    assert pkt[IP].src == "1.2.3.4"
    assert pkt[IP].dst == "5.6.7.8"


def test_add_then_modify_vlan(handler):
    fp = handler.generate_pcap("tcp", 1, None, {})["filepath"]
    added = handler.add_vlan(fp, 0, 50)
    assert added["success"]
    mod = added["modified_filepath"]
    changed = handler.modify_vlan(mod, 0, 77)
    assert changed["success"]
    from scapy.all import rdpcap, Dot1Q
    assert rdpcap(changed["modified_filepath"])[0][Dot1Q].vlan == 77


# --------------------------------------------------------------------------- #
#  Bulk incremental
# --------------------------------------------------------------------------- #
def test_bulk_incremental_src_ip(handler):
    fp = handler.generate_pcap("tcp", 1, None, {})["filepath"]  # one TCP flow (>=8 pkts)
    n = len(handler.read_pcap(fp))
    indices = list(range(n))
    out = handler.bulk_modify_packets(
        fp, indices,
        {"src_ip": "10.0.0.1"},
        incremental={"enabled": True, "step": 1, "fields": ["src_ip"]},
    )
    assert out["success"], out
    from scapy.all import rdpcap, IP
    srcs = [p[IP].src for p in rdpcap(out["modified_filepath"]) if p.haslayer(IP)]
    # First selected packet gets 10.0.0.1, later ones increment.
    assert "10.0.0.1" in srcs
    assert "10.0.0.2" in srcs


# --------------------------------------------------------------------------- #
#  Structural operations
# --------------------------------------------------------------------------- #
def test_duplicate_delete_move_replicate_extract(handler):
    fp = handler.generate_pcap("tcp", 1, None, {})["filepath"]
    start = len(handler.read_pcap(fp))

    dup = handler.duplicate_packet(fp, 0)
    assert dup["success"] and dup["new_packet_count"] == start + 1

    mod = dup["modified_filepath"]
    after_del = handler.delete_packet(mod, 0)
    assert after_del["success"] and after_del["new_packet_count"] == start

    moved = handler.move_packet(mod, 0, "bottom")
    assert moved["success"]

    rep = handler.replicate_packets(mod, [0, 1], 2)
    assert rep["success"] and rep["copy_count"] == 4

    ext = handler.extract_packets(mod, [0, 1])
    assert ext["success"] and ext["packet_count"] == 2


def test_invalid_packet_index_is_rejected(handler):
    fp = handler.generate_pcap("tcp", 1, None, {})["filepath"]
    out = handler.modify_ip_addresses(fp, 9999, "1.2.3.4", None)
    assert out["success"] is False


def test_read_traversal_is_blocked(handler):
    with pytest.raises(Exception):
        handler.read_pcap("../../../../etc/passwd")

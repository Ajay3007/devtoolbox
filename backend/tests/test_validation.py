"""Network value validation tests."""
import pytest

from utils import (
    validate_ip, validate_mac, validate_port, validate_vlan,
    validate_network_fields,
)


@pytest.mark.parametrize("value", ["10.0.0.1", "192.168.1.255", "2001:db8::1", "::1"])
def test_valid_ips(value):
    assert validate_ip(value) == value


@pytest.mark.parametrize("value", ["999.1.1.1", "10.0.0", "not-an-ip", "", None])
def test_invalid_ips(value):
    with pytest.raises(ValueError):
        validate_ip(value)


@pytest.mark.parametrize("value", ["aa:bb:cc:dd:ee:ff", "00-0c-29-63-c0-fb"])
def test_valid_macs(value):
    assert validate_mac(value) == value


@pytest.mark.parametrize("value", ["zz:bb:cc:dd:ee:ff", "aa:bb:cc", "abcdef", 123])
def test_invalid_macs(value):
    with pytest.raises(ValueError):
        validate_mac(value)


def test_port_zero_is_valid():
    assert validate_port(0) == 0


@pytest.mark.parametrize("value", [-1, 65536, 70000, "abc"])
def test_invalid_ports(value):
    with pytest.raises(ValueError):
        validate_port(value)


@pytest.mark.parametrize("value", [0, 1, 4094])
def test_valid_vlans(value):
    assert validate_vlan(value) == value


@pytest.mark.parametrize("value", [-1, 4095, 5000, "x"])
def test_invalid_vlans(value):
    with pytest.raises(ValueError):
        validate_vlan(value)


def test_network_fields_skips_blank_and_none():
    # Blank/None mean "leave unchanged" — must not raise.
    validate_network_fields({"src_ip": "", "dst_ip": None, "src_mac": ""})


def test_network_fields_validates_present_values():
    validate_network_fields({"src_ip": "10.0.0.1", "dst_port": 443})
    with pytest.raises(ValueError):
        validate_network_fields({"src_ip": "10.0.0.1", "dst_ip": "bad"})


def test_network_fields_ignores_unknown_keys():
    validate_network_fields({"totally_unknown": "garbage", "src_ip": "10.0.0.1"})

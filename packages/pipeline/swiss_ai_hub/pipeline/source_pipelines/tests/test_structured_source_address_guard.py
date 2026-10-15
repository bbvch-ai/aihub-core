import socket
from collections import namedtuple

import psutil
import pytest

from swiss_ai_hub.pipeline.source_pipelines.structured_source_address_guard import StructuredSourceAddressGuard

Interface = namedtuple("Interface", "family address netmask")


@pytest.fixture
def dns(monkeypatch: pytest.MonkeyPatch) -> dict[str, list[str]]:
    """Names resolve only to what a test puts here; addresses resolve to themselves, and nothing reaches a resolver."""
    records: dict[str, list[str]] = {}
    resolve_numeric = socket.getaddrinfo

    def getaddrinfo(host: str, port: int | None, *args, **kwargs) -> list:
        if host in records:
            return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", (address, 0)) for address in records[host]]
        return resolve_numeric(host, port, flags=socket.AI_NUMERICHOST)

    monkeypatch.setattr(socket, "getaddrinfo", getaddrinfo)
    return records


def _attach(monkeypatch: pytest.MonkeyPatch, *, in_container: bool, interfaces: dict[str, list[Interface]]) -> None:
    monkeypatch.setattr(StructuredSourceAddressGuard, "_in_container", staticmethod(lambda: in_container))
    monkeypatch.setattr(psutil, "net_if_addrs", lambda: interfaces)


@pytest.fixture
def container(monkeypatch: pytest.MonkeyPatch) -> None:
    """The deployed pipeline: a container on one compose network, with loopback and an IPv6 link-local address."""
    _attach(
        monkeypatch,
        in_container=True,
        interfaces={
            "lo": [Interface(socket.AF_INET, "127.0.0.1", "255.0.0.0")],
            "eth0": [
                Interface(socket.AF_INET, "172.18.0.5", "255.255.0.0"),
                Interface(socket.AF_INET6, "fe80::42:acff:fe12:5%eth0", "ffff:ffff:ffff:ffff::"),
            ],
        },
    )


@pytest.fixture
def developer_machine(monkeypatch: pytest.MonkeyPatch) -> None:
    """The pipeline run with `dagster dev` on a laptop that sits on a company LAN."""
    _attach(
        monkeypatch,
        in_container=False,
        interfaces={"wlan0": [Interface(socket.AF_INET, "192.168.1.20", "255.255.255.0")]},
    )


class TestNames:
    @pytest.mark.parametrize("url", ["http://ferretdb:27017", "https://seaweedfs-s3/bucket", "http://nats"])
    def test_a_service_name_is_refused(self, url: str, dns: dict[str, list[str]]):
        with pytest.raises(ValueError, match="service inside the platform"):
            StructuredSourceAddressGuard.require_external(url)

    @pytest.mark.parametrize("url", ["http://localhost:8090", "http://127.0.0.1:8090", "http://[::1]:8090"])
    def test_loopback_stays_allowed_for_a_source_running_next_to_the_pipeline(
        self, url: str, dns: dict[str, list[str]], container: None
    ):
        dns["localhost"] = ["127.0.0.1"]

        StructuredSourceAddressGuard.require_external(url)

    def test_a_name_that_does_not_resolve_is_named(self, dns: dict[str, list[str]]):
        with pytest.raises(ValueError, match="'confluence.invalid' cannot be resolved"):
            StructuredSourceAddressGuard.require_external("https://confluence.invalid")

    def test_an_address_without_a_host_is_refused(self):
        with pytest.raises(ValueError, match="names no host"):
            StructuredSourceAddressGuard.require_external("https:///wiki")


class TestAddresses:
    @pytest.mark.parametrize(
        "address", ["169.254.169.254", "fe80::1", "::ffff:169.254.169.254", "0.0.0.0", "224.0.0.1"]
    )
    def test_metadata_link_local_multicast_and_unspecified_addresses_are_refused(
        self, address: str, dns: dict[str, list[str]]
    ):
        dns["wiki.example.com"] = [address]

        with pytest.raises(ValueError, match="which no external source uses"):
            StructuredSourceAddressGuard.require_external("https://wiki.example.com")

    def test_a_name_resolving_onto_the_pipelines_own_network_is_refused(
        self, dns: dict[str, list[str]], container: None
    ):
        dns["wiki.example.com"] = ["172.18.0.9"]

        with pytest.raises(ValueError, match="platform's own networks"):
            StructuredSourceAddressGuard.require_external("https://wiki.example.com")

    def test_typing_a_containers_address_is_refused_as_well(self, dns: dict[str, list[str]], container: None):
        with pytest.raises(ValueError, match="platform's own networks"):
            StructuredSourceAddressGuard.require_external("http://172.18.0.2:27017")

    def test_one_internal_address_among_several_refuses_the_name(self, dns: dict[str, list[str]], container: None):
        dns["wiki.example.com"] = ["203.0.113.10", "172.18.0.9"]

        with pytest.raises(ValueError, match="platform's own networks"):
            StructuredSourceAddressGuard.require_external("https://wiki.example.com")

    def test_a_data_center_on_a_company_network_is_allowed(self, dns: dict[str, list[str]], container: None):
        dns["confluence.corp.example"] = ["10.20.30.40"]

        StructuredSourceAddressGuard.require_external("https://confluence.corp.example")

    def test_outside_a_container_the_hosts_own_network_stays_reachable(
        self, dns: dict[str, list[str]], developer_machine: None
    ):
        dns["confluence.corp.example"] = ["192.168.1.50"]

        StructuredSourceAddressGuard.require_external("https://confluence.corp.example")

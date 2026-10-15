import socket
from ipaddress import IPv4Address, IPv4Network, IPv6Address, IPv6Network, ip_address, ip_network
from pathlib import Path
from urllib.parse import urlparse

import psutil

_CONTAINER_MARKERS = ("/.dockerenv", "/run/.containerenv")


class StructuredSourceAddressGuard:
    """Keeps a structured source's API calls away from the platform's own services.

    Whoever configures a knowledge database picks the address the pipeline calls, and the deployed pipeline sits on the
    backend, data and storage networks. So a service name, a link-local address (where cloud metadata lives) and any
    address on the networks of the pipeline's own container are refused. Loopback stays allowed, so a source running
    next to a developer's pipeline can be synced, and so do other private addresses, because Data Center instances
    usually live on a company network. The address is checked once before a sync, so a name that resolves elsewhere
    by the time of a later request is not caught.
    """

    @classmethod
    def require_external(cls, url: str) -> None:
        host = urlparse(url).hostname
        if not host:
            raise ValueError(f"'{url}' names no host.")
        if "." not in host and ":" not in host and host != "localhost":
            raise ValueError(f"'{host}' is the name of a service inside the platform, not of an external source.")
        container_networks = cls._container_networks()
        for address in cls._resolve(host):
            if address.is_link_local or address.is_multicast or address.is_unspecified:
                raise ValueError(f"'{host}' resolves to {address}, which no external source uses.")
            if any(address in network for network in container_networks):
                raise ValueError(f"'{host}' resolves to {address}, an address on the platform's own networks.")

    @staticmethod
    def _resolve(host: str) -> set[IPv4Address | IPv6Address]:
        try:
            infos = socket.getaddrinfo(host, None)
        except socket.gaierror as error:
            raise ValueError(f"'{host}' cannot be resolved.") from error
        addresses = {ip_address(str(info[4][0]).split("%")[0]) for info in infos}
        return {
            address.ipv4_mapped if isinstance(address, IPv6Address) and address.ipv4_mapped else address
            for address in addresses
        }

    @classmethod
    def _container_networks(cls) -> list[IPv4Network | IPv6Network]:
        """The networks this container is attached to. Outside a container there are none to protect, and the host's
        own LAN and VPN are exactly where a developer's Data Center lives."""
        if not cls._in_container():
            return []
        return [
            ip_network(f"{interface.address.split('%')[0]}/{cls._prefix_length(interface.netmask)}", strict=False)
            for interfaces in psutil.net_if_addrs().values()
            for interface in interfaces
            if interface.family in (socket.AF_INET, socket.AF_INET6)
            and interface.netmask
            and not ip_address(interface.address.split("%")[0]).is_loopback
        ]

    @staticmethod
    def _in_container() -> bool:
        return any(Path(marker).exists() for marker in _CONTAINER_MARKERS)

    @staticmethod
    def _prefix_length(netmask: str) -> int:
        return bin(int(ip_address(netmask))).count("1")

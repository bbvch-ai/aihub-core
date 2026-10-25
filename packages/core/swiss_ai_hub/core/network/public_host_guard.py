import ipaddress
import socket
from ipaddress import IPv4Address, IPv6Address
from typing import Annotated
from urllib.parse import urlsplit

_DEFAULT_PORTS = {"http": 80, "https": 443, "sftp": 22}


class PublicHostGuard:
    """Keeps a URL an administrator configured from pointing inside the platform.

    Source pipelines and agents sit on the networks of the platform's own services: a Docker service name such as
    ``seaweedfs-filer``, ``localhost`` or a private address would let whoever sets the URL send requests to them.
    Checked right before the connection is opened, against what the host resolves to then. Hosts the deployment
    allows are exempt, for a system reachable only on the company network.
    """

    @classmethod
    def require_public(
        cls,
        url: Annotated[str, "The URL as configured, with a scheme"],
        allowed_hosts: Annotated[frozenset[str], "Lower-case host names the deployment allows although internal"],
        allow_list_setting: Annotated[str, "Environment variable an operator extends the allowed hosts with"],
    ) -> None:
        parts = urlsplit(url)
        host = (parts.hostname or "").lower()
        if host in allowed_hosts:
            return
        internal = cls._why_internal(host, parts.port or _DEFAULT_PORTS.get(parts.scheme, 443))
        if internal:
            raise ValueError(
                f"The URL {url} points at {host or 'no host'}, {internal}; only public hosts are allowed. An operator "
                f"can allow it with {allow_list_setting}."
            )

    @classmethod
    def _why_internal(cls, host: str, port: int) -> str | None:
        """None when every address the host stands for is public."""
        try:
            literal = cls._unwrapped(ipaddress.ip_address(host))
        except ValueError:
            literal = None
        if literal is not None:
            return None if literal.is_global else "an internal address"
        if "." not in host:
            return "a name only an internal network resolves"
        internal = [address for address in cls._resolve(host, port) if not address.is_global]
        return f"which resolves to the internal address {internal[0]}" if internal else None

    @classmethod
    def _resolve(cls, host: str, port: int) -> list[IPv4Address | IPv6Address]:
        try:
            answers = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
        except socket.gaierror as unresolved:
            raise ValueError(f"The host {host} cannot be resolved.") from unresolved
        return [cls._unwrapped(ipaddress.ip_address(answer[4][0].split("%")[0])) for answer in answers]

    @staticmethod
    def _unwrapped(address: IPv4Address | IPv6Address) -> IPv4Address | IPv6Address:
        """``::ffff:10.0.0.1`` is the IPv4 address it carries."""
        return address.ipv4_mapped or address if isinstance(address, IPv6Address) else address

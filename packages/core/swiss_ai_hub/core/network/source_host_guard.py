import asyncio
import ipaddress
import socket
from ipaddress import IPv4Address, IPv6Address
from typing import Annotated
from urllib.parse import urlsplit

_DEFAULT_PORTS = {"http": 80, "https": 443}


class SourceHostGuard:
    """Keeps a source's URL from pointing inside the platform.

    An administrator sets the URL (of a knowledge database's source, or of a system an agent reads), while the
    pipeline and the agents sit on the networks of the platform's own services: a Docker service name such as
    ``seaweedfs-filer``, ``localhost`` or a private address would let that administrator send requests to them.
    Checked before every run's first request, against what the host resolves to then. Hosts the deployment allows are
    exempt, for a source reachable only on the company network.
    """

    @classmethod
    def require_public(
        cls,
        url: Annotated[str, "The source's base URL as configured"],
        allowed_hosts: Annotated[frozenset[str], "Lower-case host names the deployment allows although internal"],
        allow_list_variable: Annotated[str, "The environment variable an operator sets allowed_hosts with"],
    ) -> None:
        parts = urlsplit(url)
        host = (parts.hostname or "").lower()
        if host in allowed_hosts:
            return
        internal = cls._why_internal(host, parts.port or _DEFAULT_PORTS.get(parts.scheme, 443))
        if internal:
            raise ValueError(
                f"The source URL {url} points at {host}, {internal}; only public hosts are allowed. An operator can "
                f"allow it with {allow_list_variable}."
            )

    @classmethod
    async def require_public_async(
        cls,
        url: Annotated[str, "The source's base URL as configured"],
        allowed_hosts: Annotated[frozenset[str], "Lower-case host names the deployment allows although internal"],
        allow_list_variable: Annotated[str, "The environment variable an operator sets allowed_hosts with"],
    ) -> None:
        """The name lookup blocks, so an agent's event loop hands it to a thread."""
        await asyncio.to_thread(cls.require_public, url, allowed_hosts, allow_list_variable)

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
            raise ValueError(f"The source host {host} cannot be resolved.") from unresolved
        return [cls._unwrapped(ipaddress.ip_address(answer[4][0].split("%")[0])) for answer in answers]

    @staticmethod
    def _unwrapped(address: IPv4Address | IPv6Address) -> IPv4Address | IPv6Address:
        """``::ffff:10.0.0.1`` is the IPv4 address it carries."""
        return address.ipv4_mapped or address if isinstance(address, IPv6Address) else address

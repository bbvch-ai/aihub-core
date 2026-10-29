import socket

import pytest

from swiss_ai_hub.core.network.source_host_guard import SourceHostGuard

_PUBLIC = "93.184.216.34"


@pytest.fixture
def dns(monkeypatch: pytest.MonkeyPatch) -> dict[str, list[str]]:
    """What each host name resolves to; a name missing here does not resolve."""
    answers: dict[str, list[str]] = {}

    def getaddrinfo(host: str, port: int, **_: object) -> list[tuple]:
        if host not in answers:
            raise socket.gaierror(socket.EAI_NONAME, "Name or service not known")
        return [
            (socket.AF_INET6 if ":" in ip else socket.AF_INET, socket.SOCK_STREAM, 6, "", (ip, port))
            for ip in answers[host]
        ]

    monkeypatch.setattr("swiss_ai_hub.core.network.source_host_guard.socket.getaddrinfo", getaddrinfo)
    return answers


_ALLOW_LIST_VARIABLE = "STRUCTURED_PIPELINE_ALLOWED_PRIVATE_HOSTS"


def _require(url: str, allowed: frozenset[str] = frozenset()) -> None:
    SourceHostGuard.require_public(url, allowed, _ALLOW_LIST_VARIABLE)


class TestRefused:
    @pytest.mark.parametrize("url", ["http://seaweedfs-filer:8888", "http://api:8000/jira", "http://localhost:8094"])
    def test_a_name_without_a_domain_is_an_internal_service(self, url: str, dns: dict[str, list[str]]):
        """Docker answers its service and container names; no public host is called that."""
        with pytest.raises(ValueError, match="a name only an internal network resolves; only public hosts are allowed"):
            _require(url)

    @pytest.mark.parametrize(
        "url",
        [
            "http://10.0.0.5",
            "http://172.20.0.4:8888",
            "https://192.168.1.10/jira",
            "http://127.0.0.1:3000",
            "http://169.254.169.254/latest/meta-data",
            "http://[::1]:8080",
            "http://[fd00::1]",
            "http://[::ffff:10.0.0.1]",
            "http://100.64.0.1",
        ],
    )
    def test_an_internal_address_is_refused(self, url: str, dns: dict[str, list[str]]):
        with pytest.raises(ValueError, match="an internal address; only public hosts are allowed"):
            _require(url)

    def test_a_public_name_that_resolves_inside_is_refused(self, dns: dict[str, list[str]]):
        """A name the administrator controls can point anywhere, e.g. 10.0.0.5.nip.io."""
        dns["jira.attacker.example"] = ["10.0.0.5"]

        with pytest.raises(ValueError, match="which resolves to the internal address 10.0.0.5"):
            _require("https://jira.attacker.example")

    def test_one_internal_address_among_public_ones_is_enough(self, dns: dict[str, list[str]]):
        dns["jira.acme.ch"] = [_PUBLIC, "192.168.0.7"]

        with pytest.raises(ValueError, match="192.168.0.7"):
            _require("https://jira.acme.ch")

    def test_a_host_that_does_not_resolve_says_so(self, dns: dict[str, list[str]]):
        with pytest.raises(ValueError, match="The source host jira.acme.invalid cannot be resolved"):
            _require("https://jira.acme.invalid")

    def test_the_message_names_the_setting_that_allows_it(self, dns: dict[str, list[str]]):
        """Each caller has its own setting, so the operator is told the one that applies."""
        with pytest.raises(ValueError, match="An operator can allow it with JIRA_ALLOWED_PRIVATE_HOSTS"):
            SourceHostGuard.require_public("http://localhost:8094", frozenset(), "JIRA_ALLOWED_PRIVATE_HOSTS")

    @pytest.mark.asyncio
    async def test_the_async_check_refuses_the_same_hosts(self, dns: dict[str, list[str]]):
        dns["jira.attacker.example"] = ["10.0.0.5"]

        with pytest.raises(ValueError, match="which resolves to the internal address 10.0.0.5"):
            await SourceHostGuard.require_public_async(
                "https://jira.attacker.example", frozenset(), _ALLOW_LIST_VARIABLE
            )


class TestAllowed:
    def test_a_public_host_passes(self, dns: dict[str, list[str]]):
        dns["acme.atlassian.net"] = [_PUBLIC, "2606:4700::6810:84e5"]

        _require("https://acme.atlassian.net")

    def test_a_public_address_passes(self, dns: dict[str, list[str]]):
        _require(f"https://{_PUBLIC}/jira")

    @pytest.mark.parametrize("url", ["http://localhost:8094", "https://JIRA.intra.acme.ch/jira", "http://10.0.0.5"])
    def test_a_host_the_deployment_allows_passes_whatever_it_resolves_to(self, url: str, dns: dict[str, list[str]]):
        dns["jira.intra.acme.ch"] = ["10.1.2.3"]

        _require(url, frozenset({"localhost", "jira.intra.acme.ch", "10.0.0.5"}))

    @pytest.mark.asyncio
    async def test_the_async_check_passes_a_public_host(self, dns: dict[str, list[str]]):
        dns["acme.atlassian.net"] = [_PUBLIC]

        await SourceHostGuard.require_public_async("https://acme.atlassian.net", frozenset(), _ALLOW_LIST_VARIABLE)

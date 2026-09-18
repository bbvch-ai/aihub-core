import base64
from datetime import UTC, datetime, timedelta

import httpx
import jwt
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from swiss_ai_hub.core.incident import IncidentSettings

from swiss_ai_hub.api.routes.incident.github_issue_client import GitHubIssueClient


def _private_key_pem() -> str:
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    return key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode()


PRIVATE_KEY = _private_key_pem()


def _settings(**overrides) -> IncidentSettings:
    values = {
        "GITHUB_REPOSITORY": "bbvch-ai/aihub-incidents",
        "GITHUB_APP_ID": "4985385",
        "GITHUB_INSTALLATION_ID": "162644320",
        "GITHUB_PRIVATE_KEY": PRIVATE_KEY,
    }
    return IncidentSettings(**(values | overrides))


def _token_response(request: httpx.Request) -> httpx.Response:
    expires = (datetime.now(UTC) + timedelta(hours=1)).isoformat()
    return httpx.Response(201, json={"token": "ghs_installation", "expires_at": expires})


class _Transport(httpx.MockTransport):
    """Records every request so a test can assert on the sequence, not just the result."""

    def __init__(self, handler):
        self.requests: list[httpx.Request] = []

        def recording(request: httpx.Request) -> httpx.Response:
            self.requests.append(request)
            return handler(request)

        super().__init__(recording)


@pytest.fixture
def transport_factory(monkeypatch):
    def install(handler) -> _Transport:
        transport = _Transport(handler)
        original = httpx.AsyncClient.__init__

        def patched(self, *args, **kwargs):
            kwargs["transport"] = transport
            original(self, *args, **kwargs)

        monkeypatch.setattr(httpx.AsyncClient, "__init__", patched)
        return transport

    return install


def test_should_sign_the_app_jwt_so_github_can_verify_it() -> None:
    client = GitHubIssueClient(_settings())

    token = client._app_jwt()
    claims = jwt.decode(token, options={"verify_signature": False})

    assert claims["iss"] == "4985385"
    assert claims["exp"] - claims["iat"] <= 600, "GitHub rejects an App JWT valid for more than ten minutes"
    assert claims["iat"] < datetime.now(UTC).timestamp(), "back-dated to absorb clock skew"
    assert jwt.get_unverified_header(token)["alg"] == "RS256"


def test_should_accept_a_key_whose_newlines_arrived_escaped() -> None:
    """A dev .env holds the PEM on one line; a Docker secret holds it with real newlines."""
    settings = _settings(GITHUB_PRIVATE_KEY=PRIVATE_KEY.replace("\n", "\\n"))

    assert GitHubIssueClient(settings)._app_jwt()


@pytest.mark.asyncio
async def test_should_buy_an_installation_token_before_creating_an_issue(transport_factory) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/access_tokens"):
            return _token_response(request)
        return httpx.Response(201, json={"number": 7})

    transport = transport_factory(handler)
    issue = await GitHubIssueClient(_settings()).create_issue("t", "b", ["incident"])

    assert issue["number"] == 7
    assert [request.url.path for request in transport.requests] == [
        "/app/installations/162644320/access_tokens",
        "/repos/bbvch-ai/aihub-incidents/issues",
    ]
    assert transport.requests[1].headers["authorization"] == "Bearer ghs_installation"


@pytest.mark.asyncio
async def test_should_reuse_a_live_installation_token_instead_of_buying_one_per_call(transport_factory) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/access_tokens"):
            return _token_response(request)
        return httpx.Response(201, json={"number": 1})

    transport = transport_factory(handler)
    client = GitHubIssueClient(_settings())
    await client.create_issue("a", "b", [])
    await client.create_issue("c", "d", [])

    exchanges = [r for r in transport.requests if r.url.path.endswith("/access_tokens")]
    assert len(exchanges) == 1


@pytest.mark.asyncio
async def test_should_refuse_to_file_into_a_public_repository(transport_factory) -> None:
    """The one failure that cannot be undone: a report published to the open internet."""

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/access_tokens"):
            return _token_response(request)
        return httpx.Response(200, json={"private": False})

    transport_factory(handler)

    with pytest.raises(PermissionError, match="is public"):
        await GitHubIssueClient(_settings()).ensure_repository_is_private()


@pytest.mark.asyncio
async def test_should_accept_a_private_repository_and_only_check_once(transport_factory) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/access_tokens"):
            return _token_response(request)
        return httpx.Response(200, json={"private": True})

    transport = transport_factory(handler)
    client = GitHubIssueClient(_settings())
    await client.ensure_repository_is_private()
    await client.ensure_repository_is_private()

    lookups = [r for r in transport.requests if r.url.path == "/repos/bbvch-ai/aihub-incidents"]
    assert len(lookups) == 1


@pytest.mark.asyncio
async def test_should_commit_an_attachment_base64_encoded_and_return_its_url(transport_factory) -> None:
    captured: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/access_tokens"):
            return _token_response(request)
        captured["path"] = request.url.path
        captured["body"] = request.read()
        return httpx.Response(201, json={"content": {"download_url": "https://example.test/shot.png"}})

    transport_factory(handler)
    url = await GitHubIssueClient(_settings()).commit_attachment(
        path="attachments/INC-1/shot.png", content=b"\x89PNG bytes", message="Attach"
    )

    assert url == "https://example.test/shot.png"
    assert captured["path"] == "/repos/bbvch-ai/aihub-incidents/contents/attachments/INC-1/shot.png"
    assert base64.b64encode(b"\x89PNG bytes").decode() in captured["body"].decode()


@pytest.mark.asyncio
async def test_should_surface_a_github_rejection_rather_than_swallow_it(transport_factory) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/access_tokens"):
            return httpx.Response(404, json={"message": "Not Found"})
        return httpx.Response(201, json={})

    transport_factory(handler)

    with pytest.raises(httpx.HTTPStatusError):
        await GitHubIssueClient(_settings()).create_issue("t", "b", [])

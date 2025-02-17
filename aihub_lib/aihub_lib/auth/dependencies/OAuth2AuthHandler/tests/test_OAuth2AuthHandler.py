import os
import base64
import pytest
import jwt
import httpx
from datetime import datetime, timedelta, timezone
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization

from pytest_bdd import scenario, given, when, then, parsers
from aihub_lib.auth.AuthenticatedUser import AuthenticatedUser
from aihub_lib.auth.dependencies.OAuth2AuthHandler.OAuth2AuthHandler import OAuth2AuthHandler
from aihub_lib.auth.dependencies.OAuth2AuthHandler.OAuth2Config import OAuth2Config
from aihub_lib.testing.asyncio_utils.bdd import async_test

# -------------------------------
# Helper Functions and Classes
# -------------------------------
def base64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b'=').decode('utf-8')

def generate_rsa_keypair():
    """Generate a new RSA key pair."""
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_key = private_key.public_key()
    return private_key, public_key

def public_key_to_jwk(public_key, kid: str) -> dict:
    """Convert an RSA public key to a JWK dict."""
    numbers = public_key.public_numbers()
    n_int = numbers.n
    e_int = numbers.e
    n_bytes = n_int.to_bytes((n_int.bit_length() + 7) // 8, byteorder='big')
    e_bytes = e_int.to_bytes((e_int.bit_length() + 7) // 8, byteorder='big')
    jwk = {
        "kty": "RSA",
        "kid": kid,
        "use": "sig",
        "n": base64url_encode(n_bytes),
        "e": base64url_encode(e_bytes),
    }
    return jwk

class DummyResponse:
    """A dummy HTTPX response for JWKS requests."""
    def __init__(self, json_data, status_code=200):
        self._json = json_data
        self.status_code = status_code

    def json(self):
        return self._json

    def raise_for_status(self):
        if self.status_code >= 400:
            raise httpx.HTTPStatusError("Error", request=None, response=self)

# -------------------------------
# Scenario Declaration
# -------------------------------
@scenario("features/oauth2_auth_handler.feature", "Valid OAuth2 token returns authenticated user")
def test_valid_oauth2_token():
    pass

# -------------------------------
# Fixtures
# -------------------------------
@pytest.fixture
def oauth2_config(monkeypatch):
    """
    Set up the OAuth2 configuration via environment variables.
    """
    monkeypatch.setenv("TENANT_ID", "test-tenant")
    monkeypatch.setenv("CLIENT_ID", "test-client")
    monkeypatch.setenv("AUTHORITY_URL", "https://login.microsoftonline.com")
    return OAuth2Config()

@pytest.fixture
def rsa_keys():
    """Generate and return a test RSA key pair and a fixed key ID."""
    private_key, public_key = generate_rsa_keypair()
    kid = "test-key-id"
    jwk = public_key_to_jwk(public_key, kid)
    return {"private_key": private_key, "public_key": public_key, "kid": kid, "jwk": jwk}

@pytest.fixture
def fake_jwks_response(rsa_keys):
    """Return a fake JWKS response using the generated public key."""
    return {"keys": [rsa_keys["jwk"]]}

@pytest.fixture(autouse=True)
def monkeypatch_httpx(monkeypatch, fake_jwks_response, oauth2_config):
    """
    Monkeypatch httpx.AsyncClient.get to return a fake JWKS response.
    """
    async def fake_get(self, url, **kwargs):
        return DummyResponse(fake_jwks_response, status_code=200)
    monkeypatch.setattr(httpx.AsyncClient, "get", fake_get)

@pytest.fixture
def oauth2_context():
    """Context to store data (like the authenticated user) across steps."""
    return {}

# -------------------------------
# Given Steps
# -------------------------------
@given(parsers.parse('an OAuth2 configuration with tenant_id "{tenant_id}", client_id "{client_id}", and authority_url "{authority_url}"'))
def given_oauth2_config(monkeypatch, tenant_id, client_id, authority_url):
    monkeypatch.setenv("TENANT_ID", tenant_id)
    monkeypatch.setenv("CLIENT_ID", client_id)
    monkeypatch.setenv("AUTHORITY_URL", authority_url)

@given(
    parsers.parse('a valid OAuth2 token is generated with name "{name}", email "{email}", and roles "{roles}"'),
    target_fixture="generated_token"
)
def generated_token(oauth2_config, rsa_keys, name: str, email: str, roles: str):
    """
    Generate a valid OAuth2 JWT:
      - Uses the test RSA private key.
      - Includes claims for name, preferred_username (email), and roles.
      - Sets audience to CLIENT_ID and issuer to AUTHORITY/v2.0.
    """
    now = datetime.now(timezone.utc)
    exp = now + timedelta(minutes=10)
    payload = {
        "name": name,
        "preferred_username": email,
        "roles": [r.strip() for r in roles.split(",")],
        "aud": oauth2_config.CLIENT_ID,
        "oid": "test-oid",
        "iss": f"{oauth2_config.AUTHORITY}/v2.0",
        "exp": exp,
    }
    headers = {"kid": rsa_keys["kid"]}
    token = jwt.encode(payload, rsa_keys["private_key"], algorithm="RS256", headers=headers)
    return token

# -------------------------------
# When Step
# -------------------------------
@when("I invoke the OAuth2AuthHandler with the token")
@async_test
async def invoke_oauth2_handler(generated_token, oauth2_context):
    token = generated_token
    handler = OAuth2AuthHandler()
    user = await handler(token)
    oauth2_context["user"] = user

# -------------------------------
# Then Steps
# -------------------------------
@then(parsers.parse('the returned user should have name "{expected_name}"'))
def check_oauth2_user_name(oauth2_context, expected_name):
    user = oauth2_context.get("user")
    assert user is not None, "No user was returned by OAuth2AuthHandler"
    assert user.name == expected_name

@then(parsers.parse('the returned user should have preferred_username "{expected_email}"'))
def check_oauth2_user_email(oauth2_context, expected_email):
    user = oauth2_context.get("user")
    assert user.preferred_username == expected_email

@then(parsers.parse('the returned user should have roles "{role1}" and "{role2}"'))
def check_oauth2_user_roles(oauth2_context, role1, role2):
    user = oauth2_context.get("user")
    assert set(user.roles) == {role1, role2}

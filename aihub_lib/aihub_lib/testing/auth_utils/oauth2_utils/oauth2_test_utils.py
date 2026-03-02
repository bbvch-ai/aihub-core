import base64

import httpx
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa


def base64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("utf-8")


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
    n_bytes = n_int.to_bytes((n_int.bit_length() + 7) // 8, byteorder="big")
    e_bytes = e_int.to_bytes((e_int.bit_length() + 7) // 8, byteorder="big")
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


@pytest.fixture
def rsa_keys():
    """Generate a new RSA key pair and return it along with a fixed key ID and JWK."""
    private_key, public_key = generate_rsa_keypair()
    kid = "test-key-id"
    jwk = public_key_to_jwk(public_key, kid)
    return {"private_key": private_key, "public_key": public_key, "kid": kid, "jwk": jwk}


@pytest.fixture
def fake_jwks_response(rsa_keys):
    """Return a fake JWKS response using the generated public key."""
    return {"keys": [rsa_keys["jwk"]]}

import time

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from jwt import PyJWK
from jwt.algorithms import RSAAlgorithm
from microsoft_agents.hosting.core.authorization import JwtTokenValidator


class BotFrameworkTokenFactory:
    """Mints Bot Framework-shaped JWTs and serves their public key in place of the Microsoft JWKS endpoint."""

    BOT_FRAMEWORK_ISSUER = "https://api.botframework.com"
    TRUSTED_KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    FOREIGN_KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)

    @classmethod
    def trust_signing_key(cls, monkeypatch: pytest.MonkeyPatch) -> None:
        trusted_jwk = PyJWK(RSAAlgorithm.to_jwk(cls.TRUSTED_KEY.public_key(), as_dict=True), algorithm="RS256")

        async def _signing_key(jwks_uri: str, header: dict) -> PyJWK:
            return trusted_jwk

        monkeypatch.setattr(JwtTokenValidator._jwk_client_manager, "get_signing_key", _signing_key)

    @classmethod
    def token(
        cls, *, app_id: str, service_url: str, private_key: rsa.RSAPrivateKey | None = None, **overrides: object
    ) -> str:
        """Overrides set to `None` drop the claim."""
        now = int(time.time())
        claims = {
            "iss": cls.BOT_FRAMEWORK_ISSUER,
            "aud": app_id,
            "serviceurl": service_url,
            "nbf": now - 10,
            "exp": now + 3600,
        } | overrides
        claims = {key: value for key, value in claims.items() if value is not None}
        return jwt.encode(claims, private_key or cls.TRUSTED_KEY, algorithm="RS256", headers={"kid": "test-kid"})

    @classmethod
    def authorization_header(cls, *, app_id: str, service_url: str) -> dict[str, str]:
        return {"Authorization": f"Bearer {cls.token(app_id=app_id, service_url=service_url)}"}

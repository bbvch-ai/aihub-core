"""Generates short-lived JWTs for the OpenWebUI service account."""

import time

import jwt

SERVICE_ACCOUNT_USER_ID = "00000000-0000-4000-a000-000000000001"


class OpenWebuiTokenService:
    @staticmethod
    def generate_token(secret_key: str, ttl_seconds: int = 300) -> str:
        """Why short-lived: tokens are regenerated per API call, never stored."""
        now = int(time.time())
        return jwt.encode(
            {"id": SERVICE_ACCOUNT_USER_ID, "sub": SERVICE_ACCOUNT_USER_ID, "iat": now, "exp": now + ttl_seconds},
            secret_key,
            algorithm="HS256",
        )

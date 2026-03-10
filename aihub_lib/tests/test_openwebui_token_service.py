"""Tests for OpenWebuiTokenService — JWT generation for the service account."""

import jwt

from aihub_lib.infrastructure.openwebui.OpenWebuiTokenService import (
    SERVICE_ACCOUNT_USER_ID,
    OpenWebuiTokenService,
)

SECRET_KEY = "test-secret-key-for-jwt-signing"


class TestOpenWebuiTokenService:
    def test_generate_token_returns_decodable_jwt(self) -> None:
        token = OpenWebuiTokenService.generate_token(SECRET_KEY)

        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        assert payload["id"] == SERVICE_ACCOUNT_USER_ID
        assert payload["sub"] == SERVICE_ACCOUNT_USER_ID

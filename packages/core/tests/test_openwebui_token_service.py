"""Tests for OpenWebuiTokenService — JWT generation for the service account."""

import jwt

from swiss_ai_hub.core.infrastructure.openwebui.openwebui_token_service import OpenWebuiTokenService

SECRET_KEY = "test-secret-key-for-jwt-signing"
SERVICE_ACCOUNT_ID = "00000000-0000-4000-a000-000000000001"


class TestOpenWebuiTokenService:
    def test_generate_token_returns_decodable_jwt(self) -> None:
        token = OpenWebuiTokenService.generate_token(SECRET_KEY, user_id=SERVICE_ACCOUNT_ID)

        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        assert payload["id"] == SERVICE_ACCOUNT_ID
        assert payload["sub"] == SERVICE_ACCOUNT_ID

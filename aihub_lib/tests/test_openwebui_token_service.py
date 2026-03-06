"""Tests for OpenWebuiTokenService — JWT generation for the service account."""

import time

import jwt
import pytest

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

    def test_generate_token_respects_ttl(self) -> None:
        token = OpenWebuiTokenService.generate_token(SECRET_KEY, ttl_seconds=60)

        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        assert payload["exp"] - payload["iat"] == 60

    def test_generate_token_fails_with_wrong_secret(self) -> None:
        token = OpenWebuiTokenService.generate_token(SECRET_KEY)

        with pytest.raises(jwt.InvalidSignatureError):
            jwt.decode(token, "wrong-secret", algorithms=["HS256"])

    def test_generate_token_has_valid_timestamps(self) -> None:
        before = int(time.time())
        token = OpenWebuiTokenService.generate_token(SECRET_KEY)
        after = int(time.time())

        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        assert before <= payload["iat"] <= after
        assert payload["exp"] > payload["iat"]

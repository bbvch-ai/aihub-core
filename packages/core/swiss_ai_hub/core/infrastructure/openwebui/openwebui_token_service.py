import time

import jwt


class OpenWebuiTokenService:
    @staticmethod
    def generate_token(secret_key: str, *, user_id: str, ttl_seconds: int = 300) -> str:
        """Why short-lived: tokens are regenerated per API call, never stored."""
        now = int(time.time())
        return jwt.encode(
            {"id": user_id, "sub": user_id, "iat": now, "exp": now + ttl_seconds},
            secret_key,
            algorithm="HS256",
        )

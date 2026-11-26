from datetime import datetime

from fastapi import HTTPException, status
from swiss_ai_hub.core.auth.identity.user_identity import UserIdentity
from swiss_ai_hub.core.infrastructure import trace_fn
from swiss_ai_hub.core.persistence import BearerToken

from swiss_ai_hub.api.routes.token.dto.create_token_response import CreateTokenResponse
from swiss_ai_hub.api.routes.token.dto.token_response import TokenResponse


class TokenService:
    @staticmethod
    def create_token(name: str, expiry_date: datetime, user: UserIdentity) -> CreateTokenResponse:
        """The token string is in this response and in no other, so the caller must keep it now. Not traced:
        ``trace_fn`` records return values, and this one is a secret."""
        return CreateTokenResponse.from_entity(BearerToken.create_new_token(name, expiry_date, user.id))

    @staticmethod
    @trace_fn
    def list_tokens(user: UserIdentity) -> list[TokenResponse]:
        """Tokens belong to the user rather than a tenant, so every tenant lists the same ones."""
        return [TokenResponse.from_entity(token) for token in BearerToken.issued_to(user.id)]

    @staticmethod
    @trace_fn
    def revoke_token(token_id: str, user: UserIdentity) -> None:
        """Another user's token answers 404 like a missing one, so ids cannot be probed."""
        if not BearerToken.revoke_issued(token_id, user.id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Token not found.")

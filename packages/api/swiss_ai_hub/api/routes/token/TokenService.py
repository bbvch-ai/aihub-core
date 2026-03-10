from datetime import datetime

from swiss_ai_hub.core.auth.identity.UserIdentity import UserIdentity
from swiss_ai_hub.core.persistence.access.entities.BearerToken import BearerToken

from swiss_ai_hub.api.routes.token.dto.CreateTokenResponse import CreateTokenResponse
from swiss_ai_hub.api.routes.token.dto.TokenResponse import TokenResponse


class TokenService:
    @staticmethod
    def create_token(name: str, expiry_date: datetime, user: UserIdentity) -> CreateTokenResponse:
        """
        Creates a new API token for the authenticated user.
        Returns token information including the generated token string.
        """
        token_obj = BearerToken.create_new_token(name, expiry_date, user.id)
        return CreateTokenResponse(
            id=str(token_obj.id),
            name=token_obj.name,
            expiry_date=token_obj.expiry_date,
            token=token_obj.token,
        )

    @staticmethod
    def list_tokens(user: UserIdentity) -> list[TokenResponse]:
        """
        Lists all API tokens for the authenticated user.
        The token string is not included in the response.
        """
        tokens = BearerToken.objects.filter(user_oid=user.id)
        token_list = []
        for token in tokens:
            token_list.append(
                TokenResponse(id=str(token.id), name=token.name, expiry_date=token.expiry_date, roles=user.roles)
            )
        return token_list

    @staticmethod
    def revoke_token(token_id: str, user: UserIdentity) -> None:
        """
        Revokes (deletes) an API token if it belongs to the authenticated user.
        """
        token = BearerToken.objects.get(id=token_id, user_oid=user.id)
        token.delete()

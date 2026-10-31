from datetime import datetime

from swiss_ai_hub.core.auth.identity.user_identity import UserIdentity
from swiss_ai_hub.core.persistence.access.entities.bearer_token import BearerToken

from swiss_ai_hub.api.routes.token.dto.create_token_response import CreateTokenResponse
from swiss_ai_hub.api.routes.token.dto.token_response import TokenResponse


class TokenService:
    @staticmethod
    async def create_token(name: str, expiry_date: datetime, user: UserIdentity) -> CreateTokenResponse:
        """
        Creates a new API token for the authenticated user.
        Returns token information including the generated token string.
        """
        token_obj = await BearerToken.create_new_token(name, expiry_date, user.id)
        return CreateTokenResponse(
            id=str(token_obj.id),
            name=token_obj.name,
            expiry_date=token_obj.expiry_date,
            token=token_obj.token,
        )

    @staticmethod
    async def list_tokens(user: UserIdentity) -> list[TokenResponse]:
        """
        Lists all API tokens for the authenticated user.
        The token string is not included in the response.
        """
        tokens = await BearerToken.find_for_user(user.id)
        token_list = []
        for token in tokens:
            token_list.append(
                TokenResponse(id=str(token.id), name=token.name, expiry_date=token.expiry_date, roles=user.roles)
            )
        return token_list

    @staticmethod
    async def revoke_token(token_id: str, user: UserIdentity) -> None:
        """
        Revokes (deletes) an API token if it belongs to the authenticated user.

        Raises ValueError, with the message MongoEngine gave, for an unknown or foreign token id.
        """
        token = await BearerToken.get_for_user(token_id, user.id)
        if token is None:
            raise ValueError("BearerToken matching query does not exist.")
        await token.delete()

from datetime import datetime
from typing import List

from aihub_lib.auth.AuthenticatedUser import AuthenticatedUser
from aihub_lib.persistence.access.entities.BearerToken import ApiUser, BearerToken

from aihub_api.routes.token.dto.CreateTokenResponse import CreateTokenResponse
from aihub_api.routes.token.dto.TokenResponse import TokenResponse


class TokenService:
    @staticmethod
    def create_token(
        name: str, expiry_date: datetime, user: AuthenticatedUser, roles: List[str]
    ) -> CreateTokenResponse:
        """
        Creates a new API token for the authenticated user.
        Returns token information including the generated token string.
        """
        # Convert the authenticated user to an ApiUser instance
        api_user = ApiUser(
            oid=user.oid,
            name=user.name,
            preferred_username=user.preferred_username,
            roles=user.roles,
        )
        token_obj = BearerToken.create_new_token(name, expiry_date, api_user, roles)
        return CreateTokenResponse(
            id=str(token_obj.id),
            name=token_obj.name,
            expiry_date=token_obj.expiry_date,
            roles=token_obj.roles,
            token=token_obj.token,
        )

    @staticmethod
    def list_tokens(user: AuthenticatedUser) -> List[TokenResponse]:
        """
        Lists all API tokens for the authenticated user.
        The token string is not included in the response.
        """
        tokens = BearerToken.objects.filter(user__oid=user.oid)
        token_list = []
        for token in tokens:
            token_list.append(
                TokenResponse(
                    id=str(token.id),
                    name=token.name,
                    expiry_date=token.expiry_date,
                    roles=token.roles,
                )
            )
        return token_list

    @staticmethod
    def revoke_token(token_id: str, user: AuthenticatedUser) -> None:
        """
        Revokes (deletes) an API token if it belongs to the authenticated user.
        """
        token = BearerToken.objects.get(id=token_id, user__oid=user.oid)
        token.delete()

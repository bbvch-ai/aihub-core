import hashlib
import logging

from fastapi import HTTPException, Request, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from aihub_lib.auth.dependencies.OAuth2AuthHandler.OAuth2Config import OAuth2Config
from aihub_lib.auth.dependencies.TokenAuthHandler.TokenAuthHandler import TokenAuthHandler
from aihub_lib.auth.identity.AzureIdentityProvider.AzureIdentityProvider import AzureIdentityProvider
from aihub_lib.auth.identity.UserIdentity import UserIdentity

logger = logging.getLogger(__name__)


def hash_string_sha1(input_string):
    static_salt = "k2oj3dk2*dk2p&29dkjklUdk(3kKldi39djkd?+lfdfdf"
    hash_input = f"{static_salt}{input_string}"
    input_bytes = hash_input.encode("utf-8")
    sha1_hash = hashlib.sha1(input_bytes)
    hex_digest = sha1_hash.hexdigest()
    return hex_digest


class OpenWebuiAuthHandler(TokenAuthHandler):
    def __init__(self, identity_provider: AzureIdentityProvider):
        super().__init__(identity_provider)
        self.config = OAuth2Config()
        self.app_client_id_for_roles: str | None = self.config.CLIENT_ID

    async def __call__(
        self, request: Request, bearer_token: HTTPAuthorizationCredentials = Security(HTTPBearer())
    ) -> UserIdentity:
        await super().__call__(request, bearer_token)

        open_webui_user_name = request.headers.get("X-OpenWebUI-User-Name")
        open_webui_user_email = request.headers.get("X-OpenWebUI-User-Email")

        if not (open_webui_user_name and open_webui_user_email):
            raise HTTPException(status_code=400, detail="User identification headers missing.")

        open_webui_user_name_hashed = request.headers.get("X-OpenWebUI-User-Name-Hashed")
        open_webui_user_email_hashed = request.headers.get("X-OpenWebUI-User-Email-Hashed")

        if not (open_webui_user_name_hashed and open_webui_user_email_hashed):
            logger.warning("User identification headers present, but hash headers are missing.")
            raise HTTPException(status_code=400, detail="User identification hash headers missing.")

        computed_open_webui_name_hashed = hash_string_sha1(open_webui_user_name)
        computed_open_webui_user_email_hashed = hash_string_sha1(open_webui_user_email)

        is_hash_valid = (
            computed_open_webui_name_hashed == open_webui_user_name_hashed
            and computed_open_webui_user_email_hashed == open_webui_user_email_hashed
        )

        if not is_hash_valid:
            logger.warning("User identification headers present, but hash check FAILED.")
            raise HTTPException(status_code=401, detail="User name and email hash validation failed.")

        return await self._identity_provider.get_user_identity_by_email(open_webui_user_email)

    async def authenticate_token(self, token_str: str) -> UserIdentity:
        """
        Authenticates a user using a bearer token string directly (e.g., for WebSockets).
        """
        raise ValueError("authenticate_token() should not be called for WebSockets.")

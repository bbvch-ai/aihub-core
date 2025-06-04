import hashlib
import logging
from typing import Optional

from fastapi import HTTPException, Request, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from aihub_lib.auth.AuthenticatedUser import AuthenticatedUser
from aihub_lib.auth.azure_graph.AzureGraphService import AzureGraphService
from aihub_lib.auth.dependencies.BearerAuthHandler import BearerAuthHandler
from aihub_lib.auth.dependencies.OAuth2AuthHandler.OAuth2Config import OAuth2Config
from aihub_lib.persistence.access.entities.BearerToken import BearerToken

logger = logging.getLogger(__name__)


def hash_string_sha1(input_string):
    static_salt = "k2oj3dk2*dk2p&29dkjklUdk(3kKldi39djkd?+lfdfdf"
    hash_input = f"{static_salt}{input_string}"
    input_bytes = hash_input.encode("utf-8")
    sha1_hash = hashlib.sha1(input_bytes)
    hex_digest = sha1_hash.hexdigest()
    return hex_digest


class OpenWebuiAuthHandler(BearerAuthHandler):
    def __init__(self):
        self.graph_service = AzureGraphService()
        self.config = OAuth2Config()
        self.app_client_id_for_roles: Optional[str] = self.config.CLIENT_ID

    async def __call__(
        self, request: Request, bearer_token: HTTPAuthorizationCredentials = Security(HTTPBearer())
    ) -> AuthenticatedUser:
        token_str = bearer_token.credentials
        if not token_str:
            logger.warning("Token missing in Authorization header.")
            raise HTTPException(status_code=401, detail="Bearer token missing.")

        try:
            verified_access_token_obj = BearerToken.verify_token(token_str)
            logger.debug(f"Token verified for OID {verified_access_token_obj.user_oid}.")
        except ValueError as e:
            logger.warning(f"Token authentication failed: {e}")
            raise HTTPException(status_code=401, detail=str(e))

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

        access_token_for_graph = await self.graph_service.get_token()
        graph_user_profile_by_email = await self.graph_service.get_user_by_email(
            open_webui_user_email, access_token_for_graph
        )

        if not graph_user_profile_by_email or not graph_user_profile_by_email.get("id"):
            logger.warning("Could not resolve OpenWebUI email to a user in Graph.")
            raise HTTPException(status_code=401, detail="User from OpenWebUI header not found in directory.")

        user_oid_from_header_email = graph_user_profile_by_email["id"]
        user_oid_to_use = user_oid_from_header_email

        user_app_details = await self.graph_service.get_user_details_for_app_context(
            user_oid=user_oid_to_use, app_client_id_for_roles=self.app_client_id_for_roles
        )
        profile_from_graph = user_app_details.get("profile")
        if not profile_from_graph:
            logger.warning(f"User OID {user_oid_to_use} not found via Graph.")
            raise HTTPException(status_code=401, detail="User not found.")

        user_name_to_use = profile_from_graph.get("displayName", open_webui_user_name)
        user_email_to_use = profile_from_graph.get("userPrincipalName", open_webui_user_email)

        roles_to_use = user_app_details.get("app_roles", [])

        final_user = AuthenticatedUser(
            name=user_name_to_use,
            preferred_username=user_email_to_use,
            oid=user_oid_to_use,
            roles=roles_to_use,
        )
        return final_user

    async def authenticate_token(self, token_str: str) -> AuthenticatedUser:
        """
        Authenticates a user using a bearer token string directly (e.g., for WebSockets).
        """
        raise ValueError("authenticate_token() should not be called for WebSockets.")

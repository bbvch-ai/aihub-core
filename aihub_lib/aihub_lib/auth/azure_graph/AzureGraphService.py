import base64
import logging
from typing import Any, Dict, List, Optional

import httpx
from azure.identity.aio import DefaultAzureCredential as AsyncDefaultAzureCredential
from cachetools import TTLCache

logger = logging.getLogger(__name__)


class AzureGraphService:
    MS_GRAPH_BASE_URL = "https://graph.microsoft.com/v1.0"

    def __init__(self):
        self.credential = AsyncDefaultAzureCredential()
        self.graph_scope = "https://graph.microsoft.com/.default"
        self.user_profile_cache = TTLCache(maxsize=128, ttl=3600)
        self.profile_image_cache = TTLCache(maxsize=128, ttl=18000)
        self.service_principal_cache = TTLCache(maxsize=50, ttl=3600)
        self.app_role_assignments_cache = TTLCache(maxsize=100, ttl=600)
        self.user_app_details_cache = TTLCache(maxsize=128, ttl=600)

    async def get_token(self) -> str:
        logger.debug("AzureGraphService: Attempting to get token.")
        try:
            token_result = await self.credential.get_token(self.graph_scope)
            logger.debug(f"AzureGraphService: Token acquired. Expires on: {token_result.expires_on}")
            return token_result.token
        except Exception as e:
            logger.exception(f"AzureGraphService: Failed to acquire token: {e}")
            raise

    async def get_user_by_oid(self, user_oid: str, access_token: str) -> Optional[Dict[str, Any]]:
        cache_key = f"user_profile_{user_oid}"
        if cache_key in self.user_profile_cache:
            logger.debug(f"AzureGraphService: Cache hit for user_profile_{user_oid}.")
            return self.user_profile_cache[cache_key]

        logger.debug(f"AzureGraphService: Fetching user by OID {user_oid}.")
        user_url = f"{self.MS_GRAPH_BASE_URL}/users/{user_oid}?$select=id,displayName,mail,userPrincipalName"
        headers = {"Authorization": f"Bearer {access_token}"}

        async with httpx.AsyncClient() as client:
            response = await client.get(user_url, headers=headers)

        if response.status_code == 200:
            user_data = response.json()
            logger.debug(f"AzureGraphService: User data for OID {user_oid}: {user_data}")
            self.user_profile_cache[cache_key] = user_data
            return user_data
        elif response.status_code == 404:
            logger.warning(f"AzureGraphService: User not found for OID {user_oid} (404).")
            return None
        else:
            logger.exception(
                f"AzureGraphService: Failed to fetch user {user_oid}. Status: {response.status_code}, Response: {response.text}"
            )
            return None

    async def get_user_by_email(self, email: str, access_token: str) -> Optional[Dict[str, Any]]:
        logger.debug(f"AzureGraphService: Fetching user by email {email}.")
        search_url = f"{self.MS_GRAPH_BASE_URL}/users?$filter=mail eq '{email}' or userPrincipalName eq '{email}'&$select=id,displayName,mail,userPrincipalName"
        headers = {"Authorization": f"Bearer {access_token}"}

        async with httpx.AsyncClient() as client:
            response = await client.get(search_url, headers=headers)

        if response.status_code == 200:
            user_data_response = response.json()
            if user_data_response.get("value") and len(user_data_response["value"]) > 0:
                user = user_data_response["value"][0]
                logger.debug(f"AzureGraphService: User found by email {email}: OID {user.get('id')}")
                if user.get("id"):
                    oid_cache_key = f"user_profile_{user['id']}"
                    if oid_cache_key not in self.user_profile_cache:
                        self.user_profile_cache[oid_cache_key] = user
                return user
            else:
                logger.warning(f"AzureGraphService: No user found for email {email} in response value.")
                return None
        else:
            logger.exception(
                f"AzureGraphService: Failed to query user by email {email}. Status: {response.status_code}, Response: {response.text}"
            )
            return None

    async def get_profile_image_data_url(self, user_oid: str, access_token: str) -> Optional[str]:
        cache_key = f"profile_image_{user_oid}"
        if cache_key in self.profile_image_cache:
            logger.debug(f"AzureGraphService: Cache hit for profile_image_{user_oid}.")
            return self.profile_image_cache[cache_key]

        logger.debug(f"AzureGraphService: Fetching profile image for user OID {user_oid}.")
        image_url = f"{self.MS_GRAPH_BASE_URL}/users/{user_oid}/photo/$value"
        headers = {"Authorization": f"Bearer {access_token}"}
        image_data_url = None
        try:
            async with httpx.AsyncClient() as client:
                image_response = await client.get(image_url, headers=headers)
            if image_response.status_code == 200:
                image_content = image_response.content
                content_type = image_response.headers.get("Content-Type", "image/jpeg")
                base64_data = base64.b64encode(image_content).decode("utf-8")
                image_data_url = f"data:{content_type};base64,{base64_data}"
                logger.debug(f"AzureGraphService: Profile image successfully fetched for user OID {user_oid}.")
            elif image_response.status_code == 404:
                logger.debug(f"AzureGraphService: No profile image found for user OID {user_oid} (404).")
            else:
                logger.warning(
                    f"AzureGraphService: Failed to fetch profile image for {user_oid}. Status: {image_response.status_code}, Response: {image_response.text}"
                )
        except Exception as e:
            logger.error(f"AzureGraphService: Error fetching profile image for {user_oid}: {e}", exc_info=True)

        self.profile_image_cache[cache_key] = image_data_url
        return image_data_url

    async def _get_service_principal_by_app_id(self, app_id: str, access_token: str) -> Optional[Dict[str, Any]]:
        cache_key = f"service_principal_app_id_{app_id}"
        if cache_key in self.service_principal_cache:
            logger.debug(f"AzureGraphService: Cache hit for SP by app_id {app_id}.")
            return self.service_principal_cache[cache_key]

        logger.debug(f"AzureGraphService: Fetching SP by app_id {app_id}.")
        sp_url = f"{self.MS_GRAPH_BASE_URL}/servicePrincipals?$filter=appId eq '{app_id}'&$select=id,appId,displayName,appRoles"
        headers = {"Authorization": f"Bearer {access_token}", "ConsistencyLevel": "eventual"}
        logger.debug(f"AzureGraphService: SP by app_id URL: {sp_url}")

        async with httpx.AsyncClient() as client:
            response = await client.get(sp_url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            logger.debug(f"AzureGraphService: SP by app_id {app_id} raw data: {data}")
            value = data.get("value", [])
            if not value:
                logger.warning(f"AzureGraphService: No SP found for appID {app_id} in response value.")
                self.service_principal_cache[cache_key] = None
                return None
            sp_data = value[0]
            logger.debug(
                f"AzureGraphService: SP data for app_id {app_id}: ID={sp_data.get('id')}, AppRoles: {len(sp_data.get('appRoles',[])) > 0}"
            )
            self.service_principal_cache[cache_key] = sp_data
            return sp_data
        else:
            logger.exception(
                f"AzureGraphService: Failed to fetch SP for appID {app_id}. Status: {response.status_code}, Response: {response.text}"
            )
            self.service_principal_cache[cache_key] = None
            return None

    async def _get_user_app_role_assignment_ids_for_sp(
        self, user_oid: str, target_resource_sp_id: str, access_token: str
    ) -> List[str]:
        cache_key = f"assignments_{user_oid}_for_sp_{target_resource_sp_id}"
        if cache_key in self.app_role_assignments_cache:
            logger.debug(f"AzureGraphService: Cache hit for assignments: {cache_key}")
            return self.app_role_assignments_cache[cache_key]

        logger.debug(
            f"AzureGraphService: Getting assigned role IDs for user {user_oid} on target SP {target_resource_sp_id}."
        )
        assigned_role_ids = []
        assignments_url = (
            f"{self.MS_GRAPH_BASE_URL}/users/{user_oid}/appRoleAssignments"
            f"?$filter=resourceId eq {target_resource_sp_id}"
            f"&$select=appRoleId"
        )
        headers = {"Authorization": f"Bearer {access_token}"}
        logger.debug(f"AzureGraphService: Role assignment IDs URL: {assignments_url}")
        async with httpx.AsyncClient() as client:
            response = await client.get(assignments_url, headers=headers)
        if response.status_code == 200:
            assignments = response.json().get("value", [])
            logger.debug(
                f"AzureGraphService: Raw assignments for user {user_oid} on target SP {target_resource_sp_id}: {assignments}"
            )
            for assignment in assignments:
                app_role_id = assignment.get("appRoleId")
                if app_role_id:
                    assigned_role_ids.append(app_role_id)
            logger.debug(
                f"AzureGraphService: Parsed assigned_role_ids for user {user_oid} on target SP {target_resource_sp_id}: {assigned_role_ids}"
            )
            self.app_role_assignments_cache[cache_key] = assigned_role_ids
            return assigned_role_ids
        else:
            logger.exception(
                f"AzureGraphService: Failed to fetch app role assignment IDs for user {user_oid} and app SP {target_resource_sp_id}. "
                f"Status: {response.status_code}, URL: {assignments_url}, Response: {response.text}"
            )
            self.app_role_assignments_cache[cache_key] = []
            return []

    async def get_user_details_for_app_context(
        self,
        user_oid: str,
        app_client_id_for_roles: str,
    ) -> Dict[str, Any]:
        cache_key = f"user_details_app_context_{user_oid}_for_app_{app_client_id_for_roles}"
        if cache_key in self.user_app_details_cache:
            logger.debug(f"AzureGraphService: Cache hit for user_details_app_context: {cache_key}")
            return self.user_app_details_cache[cache_key]

        logger.info(
            f"AzureGraphService: Getting user details for OID {user_oid} in context of app client_id {app_client_id_for_roles}."
        )

        access_token = await self.get_token()

        user_profile = await self.get_user_by_oid(user_oid, access_token)
        profile_image_url = await self.get_profile_image_data_url(user_oid, access_token)

        app_roles_for_user: List[str] = []

        if not user_profile:
            logger.warning(f"AzureGraphService: User profile not found for OID {user_oid}. Cannot fetch app roles.")
            details = {"profile": None, "image_url": profile_image_url, "app_roles": []}
            self.user_app_details_cache[cache_key] = details
            return details

        logger.debug(
            f"AzureGraphService: Fetching SP for app client_id {app_client_id_for_roles} to get its role definitions."
        )
        app_sp_data = await self._get_service_principal_by_app_id(app_client_id_for_roles, access_token)

        if app_sp_data and app_sp_data.get("id"):
            target_app_sp_id = app_sp_data["id"]
            logger.debug(
                f"AzureGraphService: Target app SP ID is {target_app_sp_id}. App roles defined on SP: {app_sp_data.get('appRoles')}"
            )

            app_role_definitions: Dict[str, str] = {}
            for role_def in app_sp_data.get("appRoles", []):
                if role_def.get("isEnabled"):
                    role_id = role_def.get("id")
                    identifier = role_def.get("value") or role_def.get("displayName")
                    if role_id and identifier:
                        app_role_definitions[role_id] = identifier

            logger.debug(
                f"AzureGraphService: Enabled role definitions for app {app_client_id_for_roles} (SP {target_app_sp_id}): {app_role_definitions}"
            )

            if not app_role_definitions:
                logger.info(
                    f"AzureGraphService: No enabled app roles defined for app {app_client_id_for_roles} (SP ID {target_app_sp_id})."
                )
            else:
                assigned_role_ids = await self._get_user_app_role_assignment_ids_for_sp(
                    user_oid=user_oid, target_resource_sp_id=target_app_sp_id, access_token=access_token
                )
                logger.debug(
                    f"AzureGraphService: Role IDs assigned to user {user_oid} for app SP {target_app_sp_id}: {assigned_role_ids}"
                )

                for role_id in assigned_role_ids:
                    role_name = app_role_definitions.get(role_id)
                    if role_name:
                        app_roles_for_user.append(role_name)
                    else:
                        logger.warning(
                            f"AzureGraphService: Assigned role_id {role_id} for user {user_oid} on app SP {target_app_sp_id} not found in app's role definitions or was disabled."
                        )
        else:
            logger.warning(
                f"AzureGraphService: Could not find Service Principal for app client_id {app_client_id_for_roles}. Cannot determine app-specific roles."
            )

        logger.info(
            f"AzureGraphService: Final app_roles for user {user_oid} in context of app {app_client_id_for_roles}: {app_roles_for_user}"
        )

        details = {
            "profile": user_profile,
            "image_url": profile_image_url,
            "app_roles": sorted(list(set(app_roles_for_user))),
        }
        self.user_app_details_cache[cache_key] = details
        return details

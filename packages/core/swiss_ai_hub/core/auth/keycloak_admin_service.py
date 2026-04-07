import logging

from keycloak import KeycloakAdmin, KeycloakGetError

from swiss_ai_hub.core.auth.dependencies.keycloak_auth_handler.keycloak_settings import KeycloakSettings
from swiss_ai_hub.core.infrastructure.opentelemetry.tracing.decorators.trace_fn import trace_fn

logger = logging.getLogger(__name__)

TENANTS_GROUP_PATH = "/tenants"


def _create_admin() -> KeycloakAdmin:
    settings = KeycloakSettings()
    return KeycloakAdmin(
        server_url=settings.URL,
        realm_name=settings.REALM,
        client_id=settings.API_SERVICE_CLIENT_ID,
        client_secret_key=settings.API_SERVICE_CLIENT_SECRET,
    )


class KeycloakAdminService:
    """Wraps Keycloak Admin API for user and group management."""

    @staticmethod
    @trace_fn
    async def find_user_by_email(email: str) -> dict | None:
        admin = _create_admin()
        users = await admin.a_get_users(query={"email": email, "exact": True})
        return users[0] if users else None

    @staticmethod
    @trace_fn
    async def create_user(email: str) -> str:
        admin = _create_admin()
        user_id = await admin.a_create_user(
            {"email": email, "username": email, "enabled": True},
            exist_ok=True,
        )
        return user_id

    @staticmethod
    @trace_fn
    async def get_user_by_id(keycloak_user_id: str) -> dict:
        admin = _create_admin()
        return await admin.a_get_user(keycloak_user_id)

    @staticmethod
    @trace_fn
    async def get_users_by_ids(keycloak_user_ids: list[str]) -> dict[str, dict]:
        admin = _create_admin()
        result: dict[str, dict] = {}
        for user_id in keycloak_user_ids:
            try:
                user = await admin.a_get_user(user_id)
                result[user_id] = user
            except KeycloakGetError:
                logger.warning("User %s not found in Keycloak", user_id)
        return result

    @staticmethod
    @trace_fn
    async def get_tenant_group(tenant_id: str) -> dict:
        admin = _create_admin()
        return await admin.a_get_group_by_path(f"{TENANTS_GROUP_PATH}/{tenant_id}")

    @staticmethod
    @trace_fn
    async def assign_user_to_tenant(keycloak_user_id: str, tenant_id: str) -> None:
        admin = _create_admin()
        group = await admin.a_get_group_by_path(f"{TENANTS_GROUP_PATH}/{tenant_id}")
        await admin.a_group_user_add(keycloak_user_id, group["id"])

    @staticmethod
    @trace_fn
    async def remove_user_from_tenant(keycloak_user_id: str, tenant_id: str) -> None:
        admin = _create_admin()
        group = await admin.a_get_group_by_path(f"{TENANTS_GROUP_PATH}/{tenant_id}")
        await admin.a_group_user_remove(keycloak_user_id, group["id"])

    @staticmethod
    @trace_fn
    async def get_tenant_members(tenant_id: str, offset: int = 0, limit: int = 20) -> list[dict]:
        admin = _create_admin()
        group = await admin.a_get_group_by_path(f"{TENANTS_GROUP_PATH}/{tenant_id}")
        return await admin.a_get_group_members(group["id"], query={"first": offset, "max": limit})

    @staticmethod
    @trace_fn
    async def create_tenant_group(tenant_id: str) -> str | None:
        admin = _create_admin()
        parent = await admin.a_get_group_by_path(TENANTS_GROUP_PATH)
        return await admin.a_create_group({"name": tenant_id}, parent=parent["id"], skip_exists=True)

    @staticmethod
    @trace_fn
    async def delete_tenant_group(tenant_id: str) -> None:
        admin = _create_admin()
        group = await admin.a_get_group_by_path(f"{TENANTS_GROUP_PATH}/{tenant_id}")
        await admin.a_delete_group(group["id"])

    @staticmethod
    @trace_fn
    async def get_active_tenant_id(user_id: str) -> str | None:
        """Reads the active_tenant_id custom attribute from the Keycloak user."""
        admin = _create_admin()
        user = await admin.a_get_user(user_id)
        attributes = user.get("attributes", {})
        active_tenant = attributes.get("active_tenant_id", [])
        return active_tenant[0] if active_tenant else None

    @staticmethod
    @trace_fn
    async def set_active_tenant(user_id: str, tenant_id: str | None) -> None:
        """Writes the active_tenant_id custom attribute on the Keycloak user."""
        admin = _create_admin()
        value = [tenant_id] if tenant_id else []
        await admin.a_update_user(user_id, {"attributes": {"active_tenant_id": value}})

    @staticmethod
    @trace_fn
    async def clear_active_tenant_for_users_in_tenant(tenant_id: str) -> None:
        """Clears active_tenant_id for all members of a tenant group."""
        admin = _create_admin()
        try:
            group = await admin.a_get_group_by_path(f"{TENANTS_GROUP_PATH}/{tenant_id}")
        except KeycloakGetError:
            logger.warning("Tenant group %s not found, skipping active tenant cleanup", tenant_id)
            return

        members = await admin.a_get_group_members(group["id"], query={"first": 0, "max": 1000})
        for member in members:
            attributes = member.get("attributes", {})
            active_tenant = attributes.get("active_tenant_id", [])
            if active_tenant:
                await admin.a_update_user(member["id"], {"attributes": {"active_tenant_id": []}})

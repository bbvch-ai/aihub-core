import logging

from keycloak import KeycloakAdmin, KeycloakGetError

from swiss_ai_hub.core.auth.keycloak.keycloak_settings import KeycloakSettings
from swiss_ai_hub.core.auth.keycloak.models.keycloak_group import KeycloakGroup
from swiss_ai_hub.core.auth.keycloak.models.keycloak_user import KeycloakUser
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
    async def find_user_by_email(email: str) -> KeycloakUser | None:
        admin = _create_admin()
        users = await admin.a_get_users(query={"email": email, "exact": True})
        return KeycloakUser.model_validate(users[0]) if users else None

    @staticmethod
    @trace_fn
    async def get_all_users(max_results: int = 1000) -> list[KeycloakUser]:
        admin = _create_admin()
        users = await admin.a_get_users(query={"max": max_results})
        return [KeycloakUser.model_validate(u) for u in users]

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
    async def get_user_by_id(keycloak_user_id: str) -> KeycloakUser:
        admin = _create_admin()
        data = await admin.a_get_user(keycloak_user_id)
        return KeycloakUser.model_validate(data)

    @staticmethod
    @trace_fn
    async def get_users_by_ids(keycloak_user_ids: list[str]) -> dict[str, KeycloakUser]:
        admin = _create_admin()
        result: dict[str, KeycloakUser] = {}
        for user_id in keycloak_user_ids:
            try:
                data = await admin.a_get_user(user_id)
                result[user_id] = KeycloakUser.model_validate(data)
            except KeycloakGetError:
                logger.warning("User %s not found in Keycloak", user_id)
        return result

    @staticmethod
    @trace_fn
    async def get_tenant_group(tenant_id: str) -> KeycloakGroup:
        admin = _create_admin()
        data = await admin.a_get_group_by_path(f"{TENANTS_GROUP_PATH}/{tenant_id}")
        return KeycloakGroup.model_validate(data)

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
    async def get_tenant_members(tenant_id: str, offset: int = 0, limit: int = 20) -> list[KeycloakUser]:
        admin = _create_admin()
        group = await admin.a_get_group_by_path(f"{TENANTS_GROUP_PATH}/{tenant_id}")
        members = await admin.a_get_group_members(group["id"], query={"first": offset, "max": limit})
        return [KeycloakUser.model_validate(m) for m in members]

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
    async def ensure_user_profile_attributes() -> None:
        """Ensures the Keycloak user profile allows the active_tenant_id attribute.

        Keycloak 26+ rejects unmanaged attributes by default. The upConfig in the
        realm import file is not applied by Keycloak's user profile engine, so we
        configure it via the User Profile Admin API at startup instead.
        """
        admin = _create_admin()
        profile = await admin.a_get_realm_users_profile()

        attr_names = [a["name"] for a in profile.get("attributes", [])]
        if "active_tenant_id" in attr_names:
            logger.debug("User profile already has active_tenant_id attribute")
            return

        profile.setdefault("attributes", []).append(
            {
                "name": "active_tenant_id",
                "displayName": "Active Tenant ID",
                "permissions": {"view": ["admin"], "edit": ["admin"]},
                "annotations": {"inputType": "text"},
                "group": "user-metadata",
            }
        )
        profile["unmanagedAttributePolicy"] = "ADMIN_EDIT"

        await admin.a_update_realm_users_profile(profile)
        logger.info("Configured Keycloak user profile with active_tenant_id attribute")

    @staticmethod
    @trace_fn
    async def get_active_tenant_id(user_id: str) -> str | None:
        """Reads the active_tenant_id custom attribute from the Keycloak user."""
        admin = _create_admin()
        data = await admin.a_get_user(user_id)
        user = KeycloakUser.model_validate(data)
        active_tenant = user.attributes.get("active_tenant_id", [])
        return active_tenant[0] if active_tenant else None

    @staticmethod
    @trace_fn
    async def set_active_tenant(user_id: str, tenant_id: str) -> None:
        """Writes the active_tenant_id custom attribute on the Keycloak user.

        Uses GET-merge-PUT to preserve existing user data and satisfy Keycloak's
        user profile validation.
        """
        admin = _create_admin()
        user = await admin.a_get_user(user_id)
        attributes = user.get("attributes", {})
        attributes["active_tenant_id"] = [tenant_id]
        user["attributes"] = attributes
        await admin.a_update_user(user_id, user)

        verification = await admin.a_get_user(user_id)
        persisted = verification.get("attributes", {}).get("active_tenant_id", [])
        if not persisted or persisted[0] != tenant_id:
            raise RuntimeError(
                f"Failed to persist active_tenant_id={tenant_id} on Keycloak user {user_id}. "
                f"Keycloak returned attributes={verification.get('attributes')}. "
                "Check that the User Profile config allows the active_tenant_id attribute."
            )

    @staticmethod
    @trace_fn
    async def clear_active_tenant(user_id: str) -> None:
        """Removes the active_tenant_id custom attribute from the Keycloak user."""
        admin = _create_admin()
        user = await admin.a_get_user(user_id)
        attributes = user.get("attributes", {})
        attributes.pop("active_tenant_id", None)
        user["attributes"] = attributes
        await admin.a_update_user(user_id, user)

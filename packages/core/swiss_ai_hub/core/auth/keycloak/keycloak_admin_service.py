import logging
from functools import lru_cache

from keycloak import KeycloakAdmin, KeycloakGetError

from swiss_ai_hub.core.auth.keycloak.keycloak_settings import KeycloakSettings
from swiss_ai_hub.core.auth.keycloak.models.keycloak_group import KeycloakGroup
from swiss_ai_hub.core.auth.keycloak.models.keycloak_user import KeycloakUser
from swiss_ai_hub.core.auth.superuser_settings import SuperuserSettings
from swiss_ai_hub.core.infrastructure.opentelemetry.tracing.decorators.trace_fn import trace_fn

logger = logging.getLogger(__name__)

TENANTS_GROUP_PATH = "/tenants"

_superuser_id_cache: str | None = None


@lru_cache(maxsize=1)
def _create_admin() -> KeycloakAdmin:
    """Returns a process-wide singleton KeycloakAdmin.

    python-keycloak caches the access token inside the connection and refreshes it
    automatically, so reusing a single instance avoids a client-credentials round-trip
    on every Admin API call (critical for the auth hot path).
    """
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
    async def get_all_tenant_groups() -> list[KeycloakGroup]:
        """Returns all direct children of the /tenants/ parent group.

        Filters out malformed children with empty names (occasionally produced
        by the realm import when /tenants/ itself gets a zero-length subgroup).
        """
        admin = _create_admin()
        parent = await admin.a_get_group_by_path(TENANTS_GROUP_PATH)
        children = await admin.a_get_group_children(parent["id"])
        return [KeycloakGroup.model_validate(c) for c in children if c.get("name")]

    @staticmethod
    @trace_fn
    async def get_tenant_group(tenant_id: str) -> KeycloakGroup:
        admin = _create_admin()
        data = await admin.a_get_group_by_path(f"{TENANTS_GROUP_PATH}/{tenant_id}")
        return KeycloakGroup.model_validate(data)

    @staticmethod
    @trace_fn
    async def tenant_exists(tenant_id: str) -> bool:
        """Whether the Keycloak group ``/tenants/<tenant_id>`` exists.

        Keycloak is the source of truth for tenant existence; the MongoDB metadata
        collection only holds display data and must not be used to decide existence.
        """
        try:
            await KeycloakAdminService.get_tenant_group(tenant_id)
            return True
        except KeycloakGetError:
            return False

    @staticmethod
    @trace_fn
    async def filter_existing_tenant_ids(tenant_ids: list[str]) -> set[str]:
        """Returns the subset of ``tenant_ids`` whose Keycloak groups currently exist."""
        existing = await KeycloakAdminService.get_all_tenant_groups()
        existing_ids = {g.name for g in existing}
        return {tid for tid in tenant_ids if tid in existing_ids}

    @staticmethod
    @trace_fn
    async def assign_user_to_tenant(keycloak_user_id: str, tenant_id: str) -> None:
        admin = _create_admin()
        group = await admin.a_get_group_by_path(f"{TENANTS_GROUP_PATH}/{tenant_id}")
        await admin.a_group_user_add(keycloak_user_id, group["id"])

    @staticmethod
    @trace_fn
    async def get_user_tenant_ids(user_id: str) -> set[str]:
        """Returns the tenant IDs the user is a member of according to Keycloak.

        Keycloak is the sole source of truth for tenant membership. The
        ``UserTenantRoleEntity`` collection only stores role assignments; an empty
        row (or no row) does not imply non-membership, and a stale row does not
        imply membership. The ``AIHubSysAdmin`` realm role grants permissions,
        not membership — the superuser has access to every tenant because they
        are explicitly added to every tenant group on creation, not because of
        any role short-circuit.
        """
        admin = _create_admin()
        groups = await admin.a_get_user_groups(user_id)
        tenant_ids: set[str] = set()
        for group in groups:
            path = group.get("path", "")
            if not path.startswith(f"{TENANTS_GROUP_PATH}/"):
                continue
            parts = path.split("/")
            if len(parts) >= 3 and parts[2]:
                tenant_ids.add(parts[2])
        return tenant_ids

    @staticmethod
    @trace_fn
    async def is_user_member_of_tenant(user_id: str, tenant_id: str) -> bool:
        """Whether the user is a member of ``/tenants/<tenant_id>`` in Keycloak."""
        return tenant_id in await KeycloakAdminService.get_user_tenant_ids(user_id)

    @staticmethod
    @trace_fn
    async def get_superuser_id() -> str:
        """Returns the Keycloak user id of the seeded superuser, looked up by email.

        Memoized for the process lifetime — the superuser identity does not change at
        runtime. A concurrent cold-start race would store the same value twice; benign.
        Raises ``RuntimeError`` if the superuser is missing from Keycloak (mirrors the
        fail-fast pattern in ``initialize_superuser_token``).
        """
        global _superuser_id_cache
        if _superuser_id_cache is not None:
            return _superuser_id_cache

        settings = SuperuserSettings()
        keycloak_user = await KeycloakAdminService.find_user_by_email(settings.EMAIL)
        if not keycloak_user:
            raise RuntimeError(
                f"Superuser not found in Keycloak (email={settings.EMAIL}). "
                "Ensure the realm import creates a user with this email."
            )
        _superuser_id_cache = keycloak_user.id
        return _superuser_id_cache

    @staticmethod
    @trace_fn
    async def assign_superuser_to_tenant(tenant_id: str) -> None:
        """Adds the superuser to the ``/tenants/<tenant_id>`` group. Idempotent —
        Keycloak's group-add is a no-op for an existing member, which matters because
        the retryable tenant-configure flow can call this more than once."""
        superuser_id = await KeycloakAdminService.get_superuser_id()
        await KeycloakAdminService.assign_user_to_tenant(superuser_id, tenant_id)
        logger.info(f"Superuser ({SuperuserSettings().EMAIL}) assigned to tenant '{tenant_id}'")

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
    async def count_tenant_members(tenant_id: str) -> int:
        """Counts members of a tenant group.

        Keycloak has no per-group member count endpoint, so this fetches the full member
        list with brief representation (drops attributes/roles, ~10x smaller payload)
        and takes ``len()``. Linear in tenant size — watch for large tenants.
        """
        admin = _create_admin()
        group = await admin.a_get_group_by_path(f"{TENANTS_GROUP_PATH}/{tenant_id}")
        members = await admin.a_get_group_members(
            group["id"], query={"first": 0, "max": 100000, "briefRepresentation": True}
        )
        return len(members)

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
    async def get_user_realm_roles(keycloak_user_id: str) -> list[str]:
        """Returns realm role names assigned to the user. Needed when the caller
        doesn't have a JWT with a ``roles`` claim (e.g. static bearer tokens) and
        must resolve realm roles out-of-band."""
        admin = _create_admin()
        try:
            roles = await admin.a_get_realm_roles_of_user(keycloak_user_id)
        except KeycloakGetError:
            return []
        return [r["name"] for r in roles if r.get("name")]

    @staticmethod
    @trace_fn
    async def get_user_ids_with_realm_role(role_name: str) -> set[str]:
        """Returns Keycloak user IDs that have the given realm role assigned.

        Single bulk call to the realm-role-members endpoint, so role membership for
        a whole list can be resolved without one call per user. Errors propagate —
        a permission problem on the service account or an unknown role name raises
        rather than silently producing an empty set.
        """
        admin = _create_admin()
        members = await admin.a_get_realm_role_members(role_name)
        return {m["id"] for m in members if m.get("id")}

    @staticmethod
    @trace_fn
    async def get_user_ids_with_active_tenant(tenant_id: str) -> set[str]:
        """Returns the Keycloak IDs of users whose ``active_tenant_id`` attribute matches.

        Uses Keycloak's attribute search (``q=active_tenant_id:<id>``) and paginates in
        batches so there is no hard upper bound on the number of users returned.
        """
        admin = _create_admin()
        page_size = 1000
        result: set[str] = set()
        offset = 0
        while True:
            batch = await admin.a_get_users(
                query={
                    "q": f"active_tenant_id:{tenant_id}",
                    "first": offset,
                    "max": page_size,
                    "briefRepresentation": True,
                }
            )
            result.update(u["id"] for u in batch if u.get("id"))
            if len(batch) < page_size:
                break
            offset += page_size
        return result

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
        user profile validation. Notifies ``AccessChangeHook`` so downstream caches
        invalidate.
        """
        from swiss_ai_hub.core.persistence.access.access_change_hook import AccessChangeHook

        admin = _create_admin()
        user = await admin.a_get_user(user_id)
        attributes = user.get("attributes", {})
        attributes["active_tenant_id"] = [tenant_id]
        user["attributes"] = attributes
        await admin.a_update_user(user_id, user)
        AccessChangeHook.notify()

    @staticmethod
    @trace_fn
    async def ensure_active_tenant(user_id: str) -> None:
        """Ensures the user has a valid active tenant, auto-selecting one if needed.

        Keycloak is the sole source of truth for tenant membership; the candidate
        set is exactly the groups the user belongs to in Keycloak. The superuser
        naturally has every tenant available because they are explicitly added to
        every tenant group on creation — no sysadmin short-circuit.

        Selection order when no valid active tenant is set:
        1. The user's only tenant, if they have exactly one membership.
        2. The configured startup tenant (``AIHUB_STARTUP_TENANT_ID``) if the user is a member.
        3. The earliest-created tenant (by metadata timestamp) among the user's memberships.
        """
        from swiss_ai_hub.core.infrastructure.api.startup_tenant_settings import StartupTenantSettings
        from swiss_ai_hub.core.persistence.access.entities.tenant_metadata_entity import TenantMetadataEntity

        existing_tenant_ids = await KeycloakAdminService.get_user_tenant_ids(user_id)
        if not existing_tenant_ids:
            return

        current = await KeycloakAdminService.get_active_tenant_id(user_id)
        if current and current in existing_tenant_ids:
            return

        default_id = StartupTenantSettings().ID
        if len(existing_tenant_ids) == 1:
            selected_id = next(iter(existing_tenant_ids))
        elif default_id in existing_tenant_ids:
            selected_id = default_id
        else:
            earliest = TenantMetadataEntity.objects(id__in=list(existing_tenant_ids)).order_by("created_at").first()
            if earliest:
                selected_id = earliest.id
            else:
                selected_id = min(existing_tenant_ids)

        await KeycloakAdminService.set_active_tenant(user_id, selected_id)
        logger.info("Auto-selected active tenant %s for user %s", selected_id, user_id)

    @staticmethod
    @trace_fn
    async def clear_active_tenant(user_id: str) -> None:
        """Removes the active_tenant_id custom attribute from the Keycloak user.

        Notifies ``AccessChangeHook`` so downstream caches invalidate.
        """
        from swiss_ai_hub.core.persistence.access.access_change_hook import AccessChangeHook

        admin = _create_admin()
        user = await admin.a_get_user(user_id)
        attributes = user.get("attributes", {})
        attributes.pop("active_tenant_id", None)
        user["attributes"] = attributes
        await admin.a_update_user(user_id, user)
        AccessChangeHook.notify()

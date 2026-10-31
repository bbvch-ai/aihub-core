import logging
from typing import Annotated, Literal, Self

from beanie import Delete, Document, Insert, Replace, Save, SaveChanges, after_event
from pydantic import BaseModel, ConfigDict, Field, model_validator
from pymongo import ASCENDING, IndexModel

from swiss_ai_hub.core.auth.usage.usage_limit_models import RoleUsageLimit, UsageLimitPeriod
from swiss_ai_hub.core.infrastructure.opentelemetry.tracing.decorators.trace_fn import trace_fn
from swiss_ai_hub.core.persistence.access.access_change_hook import AccessChangeHook

logger = logging.getLogger(__name__)


class UsageLimit(BaseModel):
    """Pattern-based usage limit rule (NATS-style wildcards: * single-level, > multi-level)."""

    model_config = ConfigDict(extra="allow")

    pattern: str
    limit: Annotated[int, Field(ge=1)]
    period: Literal["1h", "1d", "7d", "1mo"]


class RoleEntity(Document):
    """
    Represents a role in the system, which contains a set of access rules.

    Roles are always tenant-scoped: every role belongs to exactly one tenant,
    identified by its ``tenant_id``. The default role set (``AIHubUser``,
    ``AIHubAdmin``, …) is seeded per-tenant at tenant-creation time, gated by
    ``AIHubSettings().CREATE_DEFAULT_ROLES``.

    Unknown fields are kept (`extra="allow"`): the MongoEngine document ran `strict: False`, and a role losing a
    field on rewrite would be silent data loss on the authorization path.
    """

    model_config = ConfigDict(extra="allow")

    name: str
    description: str
    access_rules: list[str] = Field(default_factory=list)
    usage_limits: list[UsageLimit] = Field(default_factory=list)
    tenant_id: str

    class Settings:
        name = "roles"
        keep_nulls = False
        use_state_management = True
        state_management_replace_objects = True
        validate_on_save = True
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("name", ASCENDING)], unique=True),
            IndexModel([("tenant_id", ASCENDING)]),
            IndexModel([("name", ASCENDING)]),
        ]

    @model_validator(mode="after")
    def _reject_duplicate_usage_limits(self) -> Self:
        """Reject duplicate (pattern, period) combinations; checked again before every save."""
        seen: set[tuple[str, str]] = set()
        for limit in self.usage_limits:
            key = (limit.pattern, limit.period)
            if key in seen:
                raise ValueError(f"Duplicate usage limit: pattern '{limit.pattern}' with period '{limit.period}'")
            seen.add(key)
        return self

    @after_event(Insert, Replace, Save, SaveChanges, Delete)
    def _resync_openwebui_access(self) -> None:
        AccessChangeHook.notify()

    @classmethod
    @trace_fn
    async def get_access_rules_for_roles(cls, role_names: list[str], tenant_id: str) -> set[str]:
        """
        Fetches all tenant-scoped roles matching the given names within the given tenant
        and returns the union of their access rules.
        """
        roles = await cls.find({"name": {"$in": list(set(role_names))}, "tenant_id": tenant_id}).to_list()
        all_rules: set[str] = set()
        for role in roles:
            all_rules.update(role.access_rules)
        return all_rules

    @classmethod
    @trace_fn
    async def filter_existing_roles(cls, role_names: list[str], tenant_id: str) -> list[str]:
        """
        Filters a list of potential role names, returning only those that exist
        as tenant-scoped roles for the given tenant.
        """
        roles = await cls.find({"name": {"$in": role_names}, "tenant_id": tenant_id}).to_list()
        return list({role.name for role in roles})

    @classmethod
    @trace_fn
    async def tenant_role_exists(cls, name: str, tenant_id: str) -> bool:
        """Whether a single named role exists within the tenant. Kept as a dedicated
        method so idempotent seeding has a stable, mockable seam."""
        return await cls.find_one({"name": name, "tenant_id": tenant_id}) is not None

    @classmethod
    @trace_fn
    async def create_tenant_role(
        cls,
        name: str,
        description: str,
        access_rules: list[str],
        tenant_id: str,
        usage_limits: list[UsageLimit] | None = None,
    ) -> Self:
        """Creates a new tenant-scoped role; raises pymongo's `DuplicateKeyError` if the tenant already has it."""
        role = cls(
            name=name,
            description=description,
            access_rules=access_rules,
            tenant_id=tenant_id,
            usage_limits=usage_limits or [],
        )
        return await role.insert()

    @classmethod
    @trace_fn
    async def get_roles_for_tenant(cls, tenant_id: str) -> list[Self]:
        """Returns all roles defined for the given tenant."""
        return await cls.find({"tenant_id": tenant_id}).sort("name").to_list()

    @classmethod
    @trace_fn
    async def list_all(cls) -> list[Self]:
        """Every role of every tenant."""
        return await cls.find().to_list()

    @classmethod
    @trace_fn
    async def get_role(cls, role_name: str, tenant_id: str) -> Self | None:
        return await cls.find_one({"name": role_name, "tenant_id": tenant_id})

    @classmethod
    @trace_fn
    async def update_role(
        cls,
        role_name: str,
        tenant_id: str,
        description: str | None = None,
        access_rules: list[str] | None = None,
    ) -> Self | None:
        """
        Updates an existing role. Returns the updated role or None if not found.

        Only provided fields are updated. Pass None to skip updating a field.
        """
        role = await cls.get_role(role_name, tenant_id)
        if not role:
            return None

        if description is not None:
            role.description = description
        if access_rules is not None:
            role.access_rules = access_rules

        await role.save_changes()
        return role

    @classmethod
    @trace_fn
    async def delete_role(cls, role_name: str, tenant_id: str) -> bool:
        """
        Deletes a role by its name and tenant_id. Returns True if deleted, False if not found.

        Also removes the role name from all UserTenantRoleEntity associations that reference it.
        """
        role = await cls.get_role(role_name, tenant_id)
        if not role:
            return False

        # Runtime import: RoleEntity ↔ UserTenantRoleEntity mutual reference for cascade deletes
        from swiss_ai_hub.core.persistence.access.entities.user_tenant_role_entity import UserTenantRoleEntity

        associations = await UserTenantRoleEntity.find({"tenant_id": tenant_id, "roles": role_name}).to_list()
        for association in associations:
            association.roles = [r for r in association.roles if r != role_name]
            await association.save_changes()

        if associations:
            logger.info(f"Removed role '{role_name}' from {len(associations)} user-tenant associations")

        await role.delete()
        return True

    @classmethod
    @trace_fn
    async def delete_role_from_all_tenants(cls, role_name: str) -> int:
        """Deletes a role by name across every tenant that defines it. Returns the count removed.

        Reuses ``delete_role`` per tenant so the ``UserTenantRoleEntity`` cascade runs. Used to
        clean up per-instance roles when the underlying agent instance is deleted.
        """
        tenant_ids = {role.tenant_id for role in await cls.find({"name": role_name}).to_list()}
        deleted = 0
        for tenant_id in tenant_ids:
            deleted += await cls.delete_role(role_name, tenant_id)
        return deleted

    @classmethod
    @trace_fn
    async def delete_roles_of_tenant(cls, tenant_id: str) -> None:
        """Deletes every role of the tenant in one query, for the tenant cascade.

        A query delete fires no document events, so the OpenWebUI re-sync MongoEngine's per-document signals gave
        is asked for here.
        """
        await cls.find({"tenant_id": tenant_id}).delete()
        AccessChangeHook.notify()

    @classmethod
    @trace_fn
    async def get_usage_limits_for_roles(cls, role_names: list[str], tenant_id: str) -> list[list[RoleUsageLimit]]:
        """Returns a list of usage_limits per role for the given tenant."""
        roles = await cls.find({"name": {"$in": role_names}, "tenant_id": tenant_id}).to_list()
        return [
            [
                RoleUsageLimit(pattern=ul.pattern, limit=ul.limit, period=UsageLimitPeriod(ul.period))
                for ul in role.usage_limits
            ]
            for role in roles
        ]

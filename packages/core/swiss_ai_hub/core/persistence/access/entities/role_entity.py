import logging
from typing import Self

from mongoengine import Document, EmbeddedDocument, EmbeddedDocumentListField, IntField, ListField, StringField
from mongoengine.errors import ValidationError

from swiss_ai_hub.core.auth.usage.usage_limit_models import RoleUsageLimit, UsageLimitPeriod
from swiss_ai_hub.core.infrastructure.opentelemetry.tracing.decorators.trace_fn import trace_fn

logger = logging.getLogger(__name__)


class UsageLimit(EmbeddedDocument):
    """Pattern-based usage limit rule (NATS-style wildcards: * single-level, > multi-level)."""

    pattern = StringField(required=True)
    limit = IntField(required=True, min_value=1)
    period = StringField(required=True, choices=["1h", "1d", "7d", "1mo"])


class RoleEntity(Document):
    """
    Represents a role in the system, which contains a set of access rules.

    Roles are always tenant-scoped: every role belongs to exactly one tenant,
    identified by its ``tenant_id``. The default role set (``AIHubUser``,
    ``AIHubAdmin``, …) is seeded per-tenant at tenant-creation time, gated by
    ``AIHubSettings().CREATE_DEFAULT_ROLES``.
    """

    meta = {
        "collection": "roles",
        "strict": False,
        "indexes": [
            {"fields": ["tenant_id", "name"], "unique": True},
            {"fields": ["tenant_id"]},
            {"fields": ["name"]},
        ],
    }

    name = StringField(required=True)
    description = StringField(required=True)
    access_rules = ListField(StringField(), default=list)
    usage_limits = EmbeddedDocumentListField(UsageLimit, default=list)
    tenant_id = StringField(required=True)

    def clean(self) -> None:
        """Reject duplicate (pattern, period) combinations in usage_limits."""
        seen: set[tuple[str, str]] = set()
        for limit in self.usage_limits:
            key = (limit.pattern, limit.period)
            if key in seen:
                raise ValidationError(f"Duplicate usage limit: pattern '{limit.pattern}' with period '{limit.period}'")
            seen.add(key)

    @classmethod
    @trace_fn
    def get_access_rules_for_roles(cls, role_names: list[str], tenant_id: str) -> set[str]:
        """
        Fetches all tenant-scoped roles matching the given names within the given tenant
        and returns the union of their access rules.
        """
        unique_role_names = list(set(role_names))

        roles_query = cls.objects(
            name__in=unique_role_names,
            tenant_id=tenant_id,
        )

        all_rules = set()
        for role in roles_query:
            all_rules.update(role.access_rules)

        return all_rules

    @classmethod
    @trace_fn
    def filter_existing_roles(cls, role_names: list[str], tenant_id: str) -> list[str]:
        """
        Filters a list of potential role names, returning only those that exist
        as tenant-scoped roles for the given tenant.
        """
        existing_roles_query = cls.objects(
            name__in=role_names,
            tenant_id=tenant_id,
        ).only("name")

        return list({role.name for role in existing_roles_query})

    @classmethod
    @trace_fn
    def tenant_role_exists(cls, name: str, tenant_id: str) -> bool:
        """Whether a single named role exists within the tenant. Kept as a dedicated
        method so idempotent seeding has a stable, mockable seam instead of inlining
        ``cls.objects(...).first()``."""
        return cls.objects(name=name, tenant_id=tenant_id).first() is not None

    @classmethod
    @trace_fn
    def create_tenant_role(
        cls,
        name: str,
        description: str,
        access_rules: list[str],
        tenant_id: str,
        usage_limits: list["UsageLimit"] | None = None,
    ) -> Self:
        """Creates a new tenant-scoped role."""
        role = cls(
            name=name,
            description=description,
            access_rules=access_rules,
            tenant_id=tenant_id,
            usage_limits=usage_limits or [],
        )
        role.save()
        return role

    @classmethod
    @trace_fn
    def get_roles_for_tenant(cls, tenant_id: str) -> list[Self]:
        """Returns all roles defined for the given tenant."""
        return list(cls.objects(tenant_id=tenant_id).order_by("name"))

    @classmethod
    @trace_fn
    def update_role(
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
        role = cls.objects(name=role_name, tenant_id=tenant_id).first()
        if not role:
            return None

        if description is not None:
            role.description = description
        if access_rules is not None:
            role.access_rules = access_rules

        role.save()
        return role

    @classmethod
    @trace_fn
    def delete_role(cls, role_name: str, tenant_id: str) -> bool:
        """
        Deletes a role by its name and tenant_id. Returns True if deleted, False if not found.

        Also removes the role name from all UserTenantRoleEntity associations that reference it.
        """
        role = cls.objects(name=role_name, tenant_id=tenant_id).first()
        if not role:
            return False

        # Runtime import: RoleEntity ↔ UserTenantRoleEntity mutual reference for cascade deletes
        from swiss_ai_hub.core.persistence.access.entities.user_tenant_role_entity import UserTenantRoleEntity

        associations = UserTenantRoleEntity.objects(tenant_id=tenant_id, roles=role_name)

        updated_count = 0
        for assoc in associations:
            assoc.roles = [r for r in assoc.roles if r != role_name]
            assoc.save()
            updated_count += 1

        if updated_count:
            logger.info(f"Removed role '{role_name}' from {updated_count} user-tenant associations")

        role.delete()
        return True

    @classmethod
    @trace_fn
    def delete_role_from_all_tenants(cls, role_name: str) -> int:
        """Deletes a role by name across every tenant that defines it. Returns the count removed.

        Reuses ``delete_role`` per tenant so the ``UserTenantRoleEntity`` cascade runs. Used to
        clean up per-instance roles when the underlying agent instance is deleted.
        """
        tenant_ids = {role.tenant_id for role in cls.objects(name=role_name).only("tenant_id")}
        return sum(1 for tenant_id in tenant_ids if cls.delete_role(role_name, tenant_id))

    @classmethod
    @trace_fn
    def get_usage_limits_for_roles(cls, role_names: list[str], tenant_id: str) -> list[list[RoleUsageLimit]]:
        """Returns a list of usage_limits per role for the given tenant."""
        roles = cls.objects(name__in=role_names, tenant_id=tenant_id).only("usage_limits")
        return [
            [
                RoleUsageLimit(pattern=ul.pattern, limit=ul.limit, period=UsageLimitPeriod(ul.period))
                for ul in role.usage_limits
            ]
            for role in roles
        ]

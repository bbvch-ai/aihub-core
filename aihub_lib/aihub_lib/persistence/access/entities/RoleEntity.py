import logging
from typing import Self

from mongoengine import Document, EmbeddedDocument, EmbeddedDocumentListField, IntField, ListField, StringField
from mongoengine.errors import ValidationError

from aihub_lib.auth.usage.usage_limit_models import RoleUsageLimit, UsageLimitPeriod
from aihub_lib.infrastructure.opentelemetry.tracing.decorators.trace_fn import trace_fn

logger = logging.getLogger(__name__)


class UsageLimit(EmbeddedDocument):
    """Pattern-based usage limit rule (NATS-style wildcards: * single-level, > multi-level)."""

    pattern = StringField(required=True)
    limit = IntField(required=True, min_value=1)
    period = StringField(required=True, choices=["1h", "1d", "7d", "1mo"])


class RoleEntity(Document):
    """
    Represents a role in the system, which contains a set of access rules.

    Roles can be either system-wide (tenant_id is None) or tenant-scoped.
    System roles are available to all tenants and are created during initialization.
    Tenant-scoped roles are created by tenant admins and only available within that tenant.
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
    tenant_id = StringField(null=True, default=None)

    @property
    def is_system_role(self) -> bool:
        """Returns True if this is a system-wide role (tenant_id is None)."""
        return self.tenant_id is None

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
    def get_system_role_by_name(cls, role_name: str) -> Self | None:
        """Fetches a system role by its name. Returns None if not found."""
        return cls.objects(name=role_name, tenant_id=None).first()

    @classmethod
    @trace_fn
    def get_access_rules_for_roles(cls, role_names: list[str], tenant_id: str) -> set[str]:
        """
        Fetches all roles corresponding to the given role names and returns a
        unique set of all their associated access rules.

        Includes both system roles (tenant_id=None) and tenant-specific roles.
        """
        unique_role_names = list(set(role_names))

        roles_query = cls.objects(
            name__in=unique_role_names,
            tenant_id__in=[None, tenant_id],
        )

        all_rules = set()
        for role in roles_query:
            all_rules.update(role.access_rules)

        return all_rules

    @classmethod
    @trace_fn
    def filter_existing_roles(cls, role_names: list[str], tenant_id: str) -> list[str]:
        """
        Filters a list of potential role names, returning only those that
        exist in the database (as system roles or tenant-specific roles).
        """
        existing_roles_query = cls.objects(
            name__in=role_names,
            tenant_id__in=[None, tenant_id],
        ).only("name")

        return list(set(role.name for role in existing_roles_query))

    @classmethod
    @trace_fn
    def create_system_role(cls, name: str, description: str, access_rules: list[str]) -> Self:
        """Creates a new system-wide role (available to all tenants)."""
        role = cls(
            name=name,
            description=description,
            access_rules=access_rules,
            tenant_id=None,
        )
        role.save()
        return role

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
        """Returns all roles available to a tenant (system roles + tenant-specific)."""
        return list(cls.objects(tenant_id__in=[None, tenant_id]).order_by("name"))

    @classmethod
    @trace_fn
    def get_system_roles(cls) -> list[Self]:
        """Returns all system-wide roles."""
        return list(cls.objects(tenant_id=None).order_by("name"))

    @classmethod
    @trace_fn
    def update_role(
        cls,
        role_name: str,
        tenant_id: str | None,
        description: str | None = None,
        access_rules: list[str] | None = None,
    ) -> Self | None:
        """
        Updates an existing role. Returns the updated role or None if not found.

        For system roles, pass tenant_id=None.
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
    def delete_role(cls, role_name: str, tenant_id: str | None) -> bool:
        """
        Deletes a role by its name and tenant_id. Returns True if deleted, False if not found.

        Also removes the role name from all UserTenantRoleEntity associations that reference it.
        For system roles, pass tenant_id=None.
        """
        role = cls.objects(name=role_name, tenant_id=tenant_id).first()
        if not role:
            return False

        # Remove the role name from all user-tenant-role associations
        from aihub_lib.persistence.access.entities.UserTenantRoleEntity import UserTenantRoleEntity

        if tenant_id:
            associations = UserTenantRoleEntity.objects(tenant_id=tenant_id, roles=role_name)
        else:
            associations = UserTenantRoleEntity.objects(roles=role_name)

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
    def get_usage_limits_for_roles(cls, role_names: list[str], tenant_id: str) -> list[list[RoleUsageLimit]]:
        """
        Returns a list of usage_limits per role.

        Includes both system roles (tenant_id=None) and tenant-specific roles.
        """
        roles = cls.objects(name__in=role_names, tenant_id__in=[None, tenant_id]).only("usage_limits")
        return [
            [
                RoleUsageLimit(pattern=ul.pattern, limit=ul.limit, period=UsageLimitPeriod(ul.period))
                for ul in role.usage_limits
            ]
            for role in roles
        ]

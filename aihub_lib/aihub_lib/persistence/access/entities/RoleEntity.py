from __future__ import annotations

from mongoengine import BooleanField, Document, EmbeddedDocument, EmbeddedDocumentListField, IntField, ListField, StringField
from mongoengine.errors import ValidationError

from aihub_lib.auth.usage.usage_limit_models import RoleUsageLimit, UsageLimitPeriod
from aihub_lib.infrastructure.opentelemetry.tracing.decorators.trace_fn import trace_fn


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
            {"fields": ["is_system_role"]},
        ],
    }

    name = StringField(required=True)
    description = StringField(required=True)
    access_rules = ListField(StringField(), default=list)
    usage_limits = EmbeddedDocumentListField(UsageLimit, default=list)
    tenant_id = StringField(null=True, default=None)
    is_system_role = BooleanField(default=False)

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
    def get_role_by_name(cls, role_name: str, tenant_id: str | None = None) -> RoleEntity | None:
        """
        Fetches a role by its name, prioritizing system roles.

        If tenant_id is provided, first searches for a tenant-specific role,
        then falls back to system roles (tenant_id is None).
        """
        if tenant_id:
            tenant_role = cls.objects(name=role_name, tenant_id=tenant_id).first()
            if tenant_role:
                return tenant_role
        return cls.objects(name=role_name, tenant_id=None).first()

    @classmethod
    @trace_fn
    def get_system_role_by_name(cls, role_name: str) -> RoleEntity | None:
        """Fetches a system role by its name. Returns None if not found."""
        return cls.objects(name=role_name, tenant_id=None).first()

    @classmethod
    @trace_fn
    def get_access_rules_for_roles(cls, role_names: list[str], tenant_id: str | None = None) -> set[str]:
        """
        Fetches all roles corresponding to the given role names and returns a
        unique set of all their associated access rules.

        Includes both system roles and tenant-specific roles if tenant_id is provided.
        """
        unique_role_names = list(set(role_names))

        if tenant_id:
            roles_query = cls.objects(
                name__in=unique_role_names,
                tenant_id__in=[None, tenant_id],
            )
        else:
            roles_query = cls.objects(name__in=unique_role_names, tenant_id=None)

        all_rules = set()
        for role in roles_query:
            all_rules.update(role.access_rules)

        return all_rules

    @classmethod
    @trace_fn
    def filter_existing_roles(cls, role_names: list[str], tenant_id: str | None = None) -> list[str]:
        """
        Filters a list of potential role names, returning only those that
        exist in the database (as system roles or tenant-specific roles).
        """
        if tenant_id:
            existing_roles_query = cls.objects(
                name__in=role_names,
                tenant_id__in=[None, tenant_id],
            ).only("name")
        else:
            existing_roles_query = cls.objects(name__in=role_names, tenant_id=None).only("name")

        return list(set(role.name for role in existing_roles_query))

    @classmethod
    @trace_fn
    def create_system_role(cls, name: str, description: str, access_rules: list[str]) -> RoleEntity:
        """Creates a new system-wide role (available to all tenants)."""
        role = cls(
            name=name,
            description=description,
            access_rules=access_rules,
            tenant_id=None,
            is_system_role=True,
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
    ) -> RoleEntity:
        """Creates a new tenant-scoped role."""
        role = cls(
            name=name,
            description=description,
            access_rules=access_rules,
            tenant_id=tenant_id,
            is_system_role=False,
        )
        role.save()
        return role

    @classmethod
    @trace_fn
    def get_roles_for_tenant(cls, tenant_id: str) -> list[RoleEntity]:
        """Returns all roles available to a tenant (system roles + tenant-specific)."""
        return list(cls.objects(tenant_id__in=[None, tenant_id]).order_by("name"))

    @classmethod
    @trace_fn
    def get_system_roles(cls) -> list[RoleEntity]:
        """Returns all system-wide roles."""
        return list(cls.objects(tenant_id=None).order_by("name"))

    @classmethod
    @trace_fn
    def get_usage_limits_for_roles(cls, role_names: list[str]) -> list[list[RoleUsageLimit]]:
        """
        Returns a list of usage_limits per role.
        """
        roles = cls.objects(name__in=role_names).only("usage_limits")
        return [
            [
                RoleUsageLimit(pattern=ul.pattern, limit=ul.limit, period=UsageLimitPeriod(ul.period))
                for ul in role.usage_limits
            ]
            for role in roles
        ]

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from mongoengine import DateTimeField, Document, ListField, StringField

from aihub_lib.infrastructure.opentelemetry.tracing.decorators.trace_fn import trace_fn


class TenantEntity(Document):
    """
    Represents a tenant (organization) in the multi-tenant system.

    Tenants provide isolation boundaries for users and roles. Each tenant has its
    own set of access rules that define the maximum scope for all users within
    that tenant. User roles are scoped to tenants, allowing users to have different
    roles in different organizations.
    """

    meta = {
        "collection": "tenants",
        "strict": False,
        "indexes": [
            {"fields": ["name"], "unique": True},
            {"fields": ["is_default"]},
        ],
    }

    id = StringField(primary_key=True, default=lambda: str(uuid4()))
    name = StringField(required=True, unique=True)
    description = StringField(default="")
    access_rules = ListField(StringField(), default=list)
    is_default = StringField(default="false")
    created_at = DateTimeField(default=lambda: datetime.now(UTC))
    updated_at = DateTimeField(default=lambda: datetime.now(UTC))

    @classmethod
    @trace_fn
    def get_tenant_by_id(cls, tenant_id: str) -> TenantEntity | None:
        """Fetches a tenant by its ID. Returns None if the tenant does not exist."""
        return cls.objects(id=tenant_id).first()

    @classmethod
    @trace_fn
    def get_tenant_by_name(cls, name: str) -> TenantEntity | None:
        """Fetches a tenant by its name. Returns None if the tenant does not exist."""
        return cls.objects(name=name).first()

    @classmethod
    @trace_fn
    def get_default_tenant(cls) -> TenantEntity | None:
        """Fetches the default tenant. Returns None if no default tenant exists."""
        return cls.objects(is_default="true").first()

    @classmethod
    @trace_fn
    def create_tenant(
        cls,
        name: str,
        description: str = "",
        access_rules: list[str] | None = None,
        is_default: bool = False,
    ) -> TenantEntity:
        """Creates a new tenant with the given parameters."""
        tenant = cls(
            name=name,
            description=description,
            access_rules=access_rules or [],
            is_default="true" if is_default else "false",
        )
        tenant.save()
        return tenant

    @classmethod
    @trace_fn
    def ensure_default_tenant_exists(
        cls,
        name: str,
        description: str = "",
        access_rules: list[str] | None = None,
    ) -> TenantEntity:
        """
        Ensures a default tenant exists, creating it if necessary.

        This is idempotent - if a default tenant already exists, it is returned.
        The default tenant has is_default set to 'true' and cannot be deleted.
        """
        existing = cls.get_default_tenant()
        if existing:
            return existing

        return cls.create_tenant(
            name=name,
            description=description,
            access_rules=access_rules,
            is_default=True,
        )

    def update_tenant(
        self,
        name: str | None = None,
        description: str | None = None,
        access_rules: list[str] | None = None,
    ) -> TenantEntity:
        """Updates the tenant with the given parameters."""
        if name is not None:
            self.name = name
        if description is not None:
            self.description = description
        if access_rules is not None:
            self.access_rules = access_rules
        self.updated_at = datetime.now(UTC)
        self.save()
        return self

    @classmethod
    @trace_fn
    def count_tenants(cls) -> int:
        """Count the total number of tenants."""
        return cls.objects.count()

    @classmethod
    @trace_fn
    def get_all_tenants(cls) -> list[TenantEntity]:
        """Get all tenants, ordered by name."""
        return list(cls.objects.order_by("name"))

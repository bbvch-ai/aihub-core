from datetime import UTC, datetime
from typing import Self

from bson import ObjectId
from mongoengine import BooleanField, DateTimeField, Document, ListField, StringField

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

    id = StringField(primary_key=True)
    name = StringField(required=True, unique=True)
    description = StringField(default="")
    access_rules = ListField(StringField(), default=list)
    is_default = BooleanField(default=False)
    created_at = DateTimeField(default=lambda: datetime.now(UTC))
    updated_at = DateTimeField(default=lambda: datetime.now(UTC))

    @classmethod
    @trace_fn
    def get_tenant_by_id(cls, tenant_id: str) -> Self | None:
        """Fetches a tenant by its ID. Returns None if the tenant does not exist."""
        return cls.objects(id=tenant_id).first()

    @classmethod
    @trace_fn
    def get_tenant_by_name(cls, name: str) -> Self | None:
        """Fetches a tenant by its name. Returns None if the tenant does not exist."""
        return cls.objects(name=name).first()

    @classmethod
    @trace_fn
    def get_default_tenant(cls) -> Self | None:
        """Fetches the default tenant. Returns None if no default tenant exists."""
        return cls.objects(is_default=True).first()

    @classmethod
    @trace_fn
    def create_tenant(
        cls,
        name: str,
        description: str = "",
        access_rules: list[str] | None = None,
        is_default: bool = False,
    ) -> Self:
        """Creates a new tenant with the given parameters."""
        tenant = cls(
            id=str(ObjectId()),
            name=name,
            description=description,
            access_rules=access_rules or [],
            is_default=is_default,
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
    ) -> Self:
        """
        Ensures a default tenant exists, creating it if necessary.

        This is idempotent - if a default tenant already exists, it is returned.
        The default tenant has is_default set to True and cannot be deleted.
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

    @classmethod
    @trace_fn
    def update_tenant(
        cls,
        tenant_id: str,
        name: str | None = None,
        description: str | None = None,
        access_rules: list[str] | None = None,
    ) -> Self | None:
        """
        Updates an existing tenant. Returns the updated tenant or None if not found.

        Only provided fields are updated. Pass None to skip updating a field.
        """
        tenant = cls.get_tenant_by_id(tenant_id)
        if not tenant:
            return None

        if name is not None:
            tenant.name = name
        if description is not None:
            tenant.description = description
        if access_rules is not None:
            tenant.access_rules = access_rules

        tenant.updated_at = datetime.now(UTC)
        tenant.save()
        return tenant

    @classmethod
    @trace_fn
    def delete_tenant(cls, tenant_id: str) -> bool:
        """
        Deletes a tenant by its ID. Returns True if deleted, False if not found.

        The default tenant cannot be deleted - attempting to do so will raise ValueError.
        """
        tenant = cls.get_tenant_by_id(tenant_id)
        if not tenant:
            return False

        if tenant.is_default:
            raise ValueError("Cannot delete the default tenant")

        tenant.delete()
        return True

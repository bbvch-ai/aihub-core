import logging
from datetime import UTC, datetime
from typing import Self
from uuid import uuid4

from mongoengine import (
    BooleanField,
    DateTimeField,
    Document,
    DoesNotExist,
    EmbeddedDocument,
    EmbeddedDocumentField,
    IntField,
    ListField,
    StringField,
)

from aihub_lib.infrastructure.opentelemetry.tracing.decorators.trace_fn import trace_fn

logger = logging.getLogger(__name__)


class DashboardItem(EmbeddedDocument):
    id = StringField(required=True)
    component = StringField(required=True)
    w = IntField()
    noResize = BooleanField()
    timeRange = StringField()
    event = StringField()
    x = IntField(required=True)
    y = IntField(required=True)
    meta = {"strict": False}


class Dashboard(EmbeddedDocument):
    minRow = IntField()
    margin = IntField()
    column = IntField()
    cellHeight = IntField()
    children = ListField(EmbeddedDocumentField(DashboardItem))
    meta = {"strict": False}


class UserEntity(Document):
    meta = {
        "collection": "users",
        "strict": False,
        "indexes": [
            {"fields": ["email"], "unique": True},
            {"fields": ["last_updated"]},
            {"fields": ["name"]},
        ],
    }
    id = StringField(primary_key=True)
    name = StringField(required=True)
    email = StringField(required=True)
    profile_image = StringField(null=True)
    last_updated = DateTimeField(required=True)
    favorite_modules = ListField(StringField(), default=list)
    dashboard = EmbeddedDocumentField(Dashboard)

    @staticmethod
    @trace_fn
    def create_default_dashboard() -> Dashboard:
        return Dashboard(
            minRow=1,
            margin=24,
            column=4,
            cellHeight=350,
            children=[
                DashboardItem(
                    id=str(uuid4()),
                    component="DashboardComponentNumber",
                    noResize=True,
                    timeRange="30d",
                    event="StartEvent",
                    x=0,
                    y=0,
                    w=1,
                ),
                DashboardItem(
                    id=str(uuid4()),
                    component="DashboardComponentLineChart",
                    noResize=True,
                    timeRange="30d",
                    event="StartEvent",
                    x=1,
                    y=0,
                    w=2,
                ),
                DashboardItem(
                    id=str(uuid4()),
                    component="DashboardComponentNumber",
                    noResize=True,
                    timeRange="30d",
                    event="ExceptionEvent",
                    x=3,
                    y=0,
                    w=1,
                ),
            ],
        )

    @classmethod
    @trace_fn
    def create_user(cls, oid: str, name: str, email: str, profile_image: str | None = None) -> Self:
        default_dashboard = cls.create_default_dashboard()
        user = cls(
            id=oid,
            name=name,
            email=email,
            profile_image=profile_image,
            favorite_modules=[],
            dashboard=default_dashboard,
            last_updated=datetime.now(UTC),
        )
        user.save()
        return user

    @trace_fn
    def get_roles(self, tenant_id: str | None = None) -> list[str]:
        """
        Retrieves the user's roles from the authoritative UserTenantRoleEntity.

        If tenant_id is None, uses the default tenant. Returns an empty list
        if no tenant assignment exists.
        """
        from aihub_lib.persistence.access.entities.TenantEntity import TenantEntity
        from aihub_lib.persistence.access.entities.UserTenantRoleEntity import UserTenantRoleEntity

        if tenant_id is None:
            default_tenant = TenantEntity.get_default_tenant()
            if not default_tenant:
                return []
            tenant_id = default_tenant.id

        return UserTenantRoleEntity.get_roles_for_user_in_tenant(self.id, tenant_id)

    @classmethod
    @trace_fn
    def ensure_user_exists(cls, oid: str, name: str, email: str, profile_image: str | None = None) -> Self:
        try:
            user = cls.objects.get(id=oid)
            user.name = name
            user.email = email
            user.profile_image = profile_image
            user.last_updated = datetime.now(UTC)
            user.save()
            return user
        except DoesNotExist:
            return cls.create_user(oid=oid, name=name, email=email, profile_image=profile_image)

    @classmethod
    @trace_fn
    def by_oid(cls, user_oid: str) -> Self:
        return cls.objects.get(id=user_oid)

    @classmethod
    @trace_fn
    def by_email(cls, email: str) -> Self:
        return cls.objects.get(email=email)

    @classmethod
    @trace_fn
    def count_users(cls) -> int:
        """Count the total number of users."""
        return cls.objects.count()

    @classmethod
    @trace_fn
    def get_paginated_users(cls, skip: int = 0, limit: int = 20) -> list["UserEntity"]:
        """Get a paginated list of users, ordered by name."""
        return cls.objects.order_by("name").skip(skip).limit(limit)

    @classmethod
    @trace_fn
    def ensure_user_exists_for_auth(
        cls,
        oid: str,
        name: str,
        email: str,
        profile_image: str | None = None,
    ) -> "UserEntity":
        """
        Ensures a user exists during authentication, with proper tenant assignment.

        For existing users: Updates profile info (name, email, image).
        For new users: Creates the user and assigns them to the default tenant with
        appropriate roles (admin roles for first user, standard roles for others).

        Roles are stored in UserTenantRoleEntity and retrieved via get_roles().
        """
        from aihub_lib.infrastructure.api.TenantSettings import TenantSettings
        from aihub_lib.persistence.access.entities.TenantEntity import TenantEntity
        from aihub_lib.persistence.access.entities.UserTenantRoleEntity import UserTenantRoleEntity

        try:
            user = cls.objects.get(id=oid)
            user.name = name
            user.email = email
            user.profile_image = profile_image
            user.last_updated = datetime.now(UTC)
            user.save()
            logger.info(f"Updated existing user: {email}")
            return user
        except DoesNotExist:
            pass

        settings = TenantSettings()
        default_tenant = TenantEntity.get_default_tenant()

        if not default_tenant:
            logger.warning("Default tenant not found. User will be created without tenant assignment.")
            return cls.create_user(oid=oid, name=name, email=email, profile_image=profile_image)

        is_first_user = cls.count_users() == 0
        if is_first_user:
            roles_to_assign = settings.first_user_signup_default_roles_list
            logger.info(f"First user signup, assigning admin roles: {roles_to_assign}")
        else:
            roles_to_assign = settings.user_signup_default_roles_list
            logger.info(f"Regular user signup, assigning default roles: {roles_to_assign}")

        user = cls.create_user(
            oid=oid,
            name=name,
            email=email,
            profile_image=profile_image,
        )

        UserTenantRoleEntity.create_or_update(
            user_id=oid,
            tenant_id=default_tenant.id,
            roles=roles_to_assign,
        )

        logger.info(f"Created new user {email} in tenant {default_tenant.name} with roles: {roles_to_assign}")
        return user

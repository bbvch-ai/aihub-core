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
    ValidationError,
)

from aihub_lib.auth.dependencies.SuperuserAuthHandler.SuperuserSettings import SuperuserSettings
from aihub_lib.infrastructure.api.UserSignupSettings import UserSignupSettings
from aihub_lib.infrastructure.opentelemetry.tracing.decorators.trace_fn import trace_fn
from aihub_lib.persistence.access.entities.TenantEntity import TenantEntity
from aihub_lib.persistence.access.entities.UserTenantRoleEntity import UserTenantRoleEntity

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
    active_tenant_id = StringField(null=True)
    last_updated = DateTimeField(required=True)
    favorite_modules = ListField(StringField(), default=list)
    dashboard = EmbeddedDocumentField(Dashboard)

    def clean(self):
        """
        Validate document fields before saving.

        Ensures profile_image is a valid URL (not a data URL or base64).
        """
        if self.profile_image and not self.profile_image.startswith(("http://", "https://")):
            raise ValidationError(
                "Profile image must be a valid http:// or https:// URL. "
                "Data URLs and base64-encoded images are not allowed."
            )

    @trace_fn
    def set_active_tenant(self, tenant_id: str) -> None:
        """Persists the user's active tenant if it changed."""
        if self.active_tenant_id == tenant_id:
            return
        self.active_tenant_id = tenant_id
        self.last_updated = datetime.now(UTC)
        self.save()

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
    def get_roles(self, tenant_id: str) -> list[str]:
        """
        Retrieves the user's roles from the authoritative UserTenantRoleEntity.

        Returns an empty list if the user has no roles in the specified tenant.
        """
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
    def get_by_ids(cls, user_ids: list[str]) -> dict[str, Self]:
        """
        Retrieve multiple users by their IDs and return as a dict.
        """
        return {u.id: u for u in cls.objects(id__in=user_ids)}

    @classmethod
    @trace_fn
    def count_users(cls, user_ids: list[str] | None = None) -> int:
        """Count the total number of users, optionally filtered by user IDs."""
        if user_ids is not None:
            return cls.objects(id__in=user_ids).count()
        return cls.objects.count()

    @classmethod
    @trace_fn
    def get_paginated_users(cls, skip: int = 0, limit: int = 20, user_ids: list[str] | None = None) -> list[Self]:
        """Get a paginated list of users, ordered by name. Optionally filtered by user IDs."""
        queryset = cls.objects(id__in=user_ids) if user_ids is not None else cls.objects
        return queryset.order_by("name").skip(skip).limit(limit)

    @classmethod
    @trace_fn
    def ensure_user_exists_for_auth(
        cls,
        oid: str,
        name: str,
        email: str,
        profile_image: str | None = None,
    ) -> Self:
        """
        Ensures a user exists during authentication, with proper tenant assignment.

        For existing users: Updates profile info (name, email, image).
        For new users: Creates the user and assigns them to the default tenant with
        appropriate roles (admin roles for first user, standard roles for others).

        Roles are stored in UserTenantRoleEntity and retrieved via get_roles().
        """
        try:
            user = cls.objects.get(id=oid)
            user.name = name
            user.email = email
            user.profile_image = profile_image
            user.last_updated = datetime.now(UTC)
            user.save()
            logger.info(f"Updated existing user: {email}")

            # Ensure user has a tenant association (repairs failed initial assignment)
            default_tenant = TenantEntity.get_default_tenant()
            if default_tenant:
                default_tenant_id = str(default_tenant.id)
                existing_roles = UserTenantRoleEntity.get_roles_for_user_in_tenant(oid, default_tenant_id)
                if not existing_roles:
                    settings = UserSignupSettings()
                    roles_to_assign = settings.regular_user_roles_list
                    UserTenantRoleEntity.create_or_update(
                        user_id=oid,
                        tenant_id=default_tenant_id,
                        roles=roles_to_assign,
                    )
                    logger.info(f"Repaired missing tenant association for user {oid} with roles: {roles_to_assign}")

            return user
        except DoesNotExist:
            pass

        settings = UserSignupSettings()
        default_tenant = TenantEntity.get_default_tenant()

        if not default_tenant:
            logger.warning("Default tenant not found. User will be created without tenant assignment.")
            return cls.create_user(oid=oid, name=name, email=email, profile_image=profile_image)

        # Exclude superuser from count when determining first "real" user
        real_user_count = cls.objects(id__ne=SuperuserSettings().OID).count()

        is_first_user = real_user_count == 0
        if is_first_user:
            roles_to_assign = settings.first_admin_user_roles_list
            logger.info(f"First user signup, assigning admin roles: {roles_to_assign}")
        else:
            roles_to_assign = settings.regular_user_roles_list
            logger.info(f"Regular user signup, assigning default roles: {roles_to_assign}")

        user = cls.create_user(
            oid=oid,
            name=name,
            email=email,
            profile_image=profile_image,
        )

        UserTenantRoleEntity.create_or_update(
            user_id=oid,
            tenant_id=str(default_tenant.id),
            roles=roles_to_assign,
        )

        user.active_tenant_id = str(default_tenant.id)
        user.save()

        logger.info(f"Created new user {email} in tenant {default_tenant.name} with roles: {roles_to_assign}")
        return user

from datetime import UTC, datetime
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
from aihub_lib.persistence.expert.ExpertGroupEntity import ExpertGroupEntity


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
            {"fields": ["roles"]},
            {"fields": ["last_updated"]},
            {"fields": ["name"]},
        ],
    }
    id = StringField(primary_key=True)
    name = StringField(required=True)
    email = StringField(required=True)
    profile_image = StringField(null=True)
    last_updated = DateTimeField(required=True)
    roles = ListField(StringField(), default=list)
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
    def create_user(
        cls, oid: str, name: str, email: str, roles: list[str], profile_image: str | None = None
    ) -> "UserEntity":
        default_dashboard = cls.create_default_dashboard()
        user = cls(
            id=oid,
            name=name,
            email=email,
            roles=roles,
            profile_image=profile_image,
            favorite_modules=[],
            dashboard=default_dashboard,
            last_updated=datetime.now(UTC),
        )
        user.save()
        return user

    @classmethod
    @trace_fn
    def ensure_user_exists(
        cls, oid: str, name: str, email: str, roles: list[str], profile_image: str | None = None
    ) -> "UserEntity":
        try:
            user = cls.objects.get(id=oid)
            user.name = name
            user.email = email
            user.roles = roles
            user.profile_image = profile_image

            user.last_updated = datetime.now(UTC)
            user.save()
        except DoesNotExist:
            user = cls.create_user(oid=oid, name=name, email=email, roles=roles, profile_image=profile_image)

        ExpertGroupEntity.add_member_to_default_group(oid)
        return user

    @classmethod
    @trace_fn
    def by_oid(cls, user_oid: str) -> "UserEntity":
        return cls.objects.get(id=user_oid)

    @classmethod
    @trace_fn
    def by_email(cls, email: str) -> "UserEntity":
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

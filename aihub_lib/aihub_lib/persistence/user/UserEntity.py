from datetime import datetime, timezone
from typing import List, Optional
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
        "indexes": [{"fields": ["email"], "unique": True}],
    }
    id = StringField(primary_key=True)
    name = StringField(required=True)
    email = StringField(required=True)
    profile_image = StringField(null=True)
    last_updated = DateTimeField(required=True)
    roles = ListField(StringField(), default=list)
    favorite_modules = ListField(StringField(), default=list)
    dashboard = EmbeddedDocumentField(Dashboard)

    @classmethod
    def _create_default_dashboard(cls) -> Dashboard:
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
    def create_user(
        cls, oid: str, name: str, email: str, roles: List[str], profile_image: Optional[str] = None
    ) -> "UserEntity":
        default_dashboard = cls._create_default_dashboard()
        user = cls(
            id=oid,
            name=name,
            email=email,
            roles=roles,
            profile_image=profile_image,
            favorite_modules=[],
            dashboard=default_dashboard,
            last_updated=datetime.now(timezone.utc),
        )
        user.save()
        return user

    @classmethod
    def ensure_user_exists(
        cls, oid: str, name: str, email: str, roles: List[str], profile_image: Optional[str] = None
    ) -> "UserEntity":
        try:
            user = cls.objects.get(id=oid)
            user.name = name
            user.email = email
            user.roles = roles
            user.profile_image = profile_image

            user.last_updated = datetime.now(timezone.utc)
            user.save()
            return user
        except DoesNotExist:
            return cls.create_user(oid=oid, name=name, email=email, roles=roles, profile_image=profile_image)

    @classmethod
    def by_oid(cls, user_oid: str) -> "UserEntity":
        return cls.objects.get(id=user_oid)

    @classmethod
    def by_email(cls, email: str) -> "UserEntity":
        return cls.objects.get(email=email)
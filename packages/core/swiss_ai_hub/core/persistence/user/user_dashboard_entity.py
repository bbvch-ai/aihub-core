from typing import Self
from uuid import uuid4

from mongoengine import (
    BooleanField,
    Document,
    DoesNotExist,
    EmbeddedDocument,
    EmbeddedDocumentField,
    IntField,
    ListField,
    StringField,
)

from swiss_ai_hub.core.infrastructure.opentelemetry.tracing.decorators.trace_fn import trace_fn


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


class UserDashboardEntity(Document):
    meta = {"collection": "user_dashboards", "strict": False}

    id = StringField(primary_key=True)
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
    def get_dashboard(cls, user_id: str) -> Dashboard | None:
        try:
            entity = cls.objects.get(id=user_id)
            return entity.dashboard
        except DoesNotExist:
            return None

    @classmethod
    @trace_fn
    def set_dashboard(cls, user_id: str, dashboard: Dashboard) -> Self:
        entity = cls.objects(id=user_id).modify(
            upsert=True,
            new=True,
            set__dashboard=dashboard,
        )
        return entity

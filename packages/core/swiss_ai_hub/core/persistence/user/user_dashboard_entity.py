from typing import Self
from uuid import uuid4

from beanie import Document
from pydantic import BaseModel, ConfigDict, Field

from swiss_ai_hub.core.infrastructure.opentelemetry.tracing.decorators.trace_fn import trace_fn


class DashboardItem(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: str
    component: str
    w: int | None = None
    noResize: bool | None = None
    timeRange: str | None = None
    event: str | None = None
    x: int
    y: int


class Dashboard(BaseModel):
    model_config = ConfigDict(extra="allow")

    minRow: int | None = None
    margin: int | None = None
    column: int | None = None
    cellHeight: int | None = None
    children: list[DashboardItem] = Field(default_factory=list)


class UserDashboardEntity(Document):
    """A user's dashboard layout, keyed by the user id.

    Unknown fields are kept (`extra="allow"`), here and in the embedded models: every MongoEngine document involved
    ran `strict: False`, and the frontend owns the layout's shape.
    """

    model_config = ConfigDict(extra="allow")

    id: str
    dashboard: Dashboard | None = None

    class Settings:
        name = "user_dashboards"
        keep_nulls = False

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
    async def get_dashboard(cls, user_id: str) -> Dashboard | None:
        entity = await cls.get(user_id)
        return entity.dashboard if entity else None

    @classmethod
    @trace_fn
    async def set_dashboard(cls, user_id: str, dashboard: Dashboard) -> Self:
        """Upserts the dashboard with a `$set` of the field alone, so fields the model does not declare survive."""
        await cls.get_pymongo_collection().update_one(
            {"_id": user_id},
            {"$set": {"dashboard": dashboard.model_dump(exclude_none=True)}},
            upsert=True,
        )
        return await cls.get(user_id)

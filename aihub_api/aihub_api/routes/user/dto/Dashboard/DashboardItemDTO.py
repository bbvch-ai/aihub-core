from typing import Annotated

from pydantic import BaseModel, Field


class DashboardItemDTO(BaseModel):
    id: Annotated[str, Field(description="Unique identifier for the dashboard widget.", min_length=1, max_length=100)]
    component: Annotated[
        str,
        Field(description="Specifies the component to render for this widget.", min_length=1, max_length=100),
    ]
    x: Annotated[int, Field(description="The x-coordinate of the widget in the grid.", ge=0, le=1000)]
    y: Annotated[int, Field(description="The y-coordinate of the widget in the grid.", ge=0, le=1000)]
    w: Annotated[
        int | None,
        Field(description="Width of the widget in grid column units.", ge=1, le=24),
    ] = None
    noResize: Annotated[
        bool | None,
        Field(description="If true, the widget cannot be resized."),
    ] = None
    timeRange: Annotated[
        str | None,
        Field(description="Time range for the data displayed in the widget.", max_length=50),
    ] = None
    event: Annotated[
        str | None,
        Field(description="The type of event data the widget displays.", max_length=100),
    ] = None

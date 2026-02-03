from typing import Annotated

from pydantic import BaseModel, Field


class DashboardItemDTO(BaseModel):
    id: Annotated[str, Field(description="Unique identifier for the dashboard widget.")]
    component: Annotated[
        str,
        Field(description="Specifies the component to render for this widget."),
    ]
    x: Annotated[int, Field(description="The x-coordinate of the widget in the grid.")]
    y: Annotated[int, Field(description="The y-coordinate of the widget in the grid.")]
    w: Annotated[
        int | None,
        Field(description="Width of the widget in grid column units."),
    ] = None
    noResize: Annotated[
        bool | None,
        Field(description="If true, the widget cannot be resized."),
    ] = None
    timeRange: Annotated[
        str | None,
        Field(description="Time range for the data displayed in the widget."),
    ] = None
    event: Annotated[
        str | None,
        Field(description="The type of event data the widget displays."),
    ] = None

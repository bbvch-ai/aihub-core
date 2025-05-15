from typing import Optional

from pydantic import BaseModel, Field
from typing_extensions import Annotated


class DashboardItemDTO(BaseModel):
    id: Annotated[
        str, Field(description="Unique identifier for the dashboard widget.")
    ]
    component: Annotated[
        str,
        Field(
            description="Specifies the component to render for this widget."
        ),
    ]
    x: Annotated[
        int, Field(description="The x-coordinate of the widget in the grid.")
    ]
    y: Annotated[
        int, Field(description="The y-coordinate of the widget in the grid.")
    ]
    w: Annotated[
        Optional[int],
        Field(description="Width of the widget in grid column units."),
    ] = None
    noResize: Annotated[
        Optional[bool],
        Field(description="If true, the widget cannot be resized."),
    ] = None
    timeRange: Annotated[
        Optional[str],
        Field(
            description="Time range for the data displayed in the widget."
        ),
    ] = None
    event: Annotated[
        Optional[str],
        Field(description="The type of event data the widget displays."),
    ] = None

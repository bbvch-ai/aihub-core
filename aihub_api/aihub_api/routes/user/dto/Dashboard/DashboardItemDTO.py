from typing import Optional
from pydantic import BaseModel, Field
from typing_extensions import Annotated

class DashboardItemDTO(BaseModel):
    id: Annotated[str, Field(description="Unique identifier for the dashboard widget, corresponds to MongoEngine's id field.")]
    component: Annotated[str, Field(description="Specifies the component to render for this widget, corresponds to MongoEngine's component field.")]
    x: Annotated[int, Field(description="The x-coordinate of the widget in the grid, corresponds to MongoEngine's x field.")]
    y: Annotated[int, Field(description="The y-coordinate of the widget in the grid, corresponds to MongoEngine's y field.")]
    w: Annotated[Optional[int], Field(description="Width of the widget in grid column units, corresponds to MongoEngine's w field.")] = None
    noResize: Annotated[Optional[bool], Field(description="If true, the widget cannot be resized, corresponds to MongoEngine's noResize field.")] = None
    timeRange: Annotated[Optional[str], Field(description="Time range for the data displayed in the widget, corresponds to MongoEngine's timeRange field.")] = None
    event: Annotated[Optional[str], Field(description="The type of event data the widget displays, corresponds to MongoEngine's event field.")] = None

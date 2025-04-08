from typing import Annotated, List

from pydantic import Field

from aihub_lib.nats.events.control.ControlEvent import ControlEvent
from aihub_lib.nats.events.display.DisplayEvent import DisplayEvent
from aihub_lib.nats.events.router.RouteOptions import RouteOptions


class RouterEvent(ControlEvent, DisplayEvent):
    routes: Annotated[List[RouteOptions], Field(..., description="List of options")]
    selected_option: Annotated[RouteOptions, Field(description="Selected option")]
    reason: Annotated[str, Field(description="Reason for the decision")]

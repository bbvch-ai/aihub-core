from typing import Annotated, ClassVar, List

from pydantic import Field

from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events.control.ControlEvent import ControlEvent
from aihub_lib.nats.events.display.DisplayEvent import DisplayEvent
from aihub_lib.nats.events.router.RouteOptions import RouteOptions


class RouterEvent(ControlEvent, DisplayEvent):
    """
    A RouterEvent marks a point where an LLM decided which way to go in the workflow.
    """

    _display_name: ClassVar[LocaleString] = LocaleString.from_i18n_path("lib.events.router_event.name")
    _display_description: ClassVar[LocaleString] = LocaleString.from_i18n_path("lib.events.router_event.description")

    routes: Annotated[List[RouteOptions], Field(..., description="List of options")]
    selected_option: Annotated[RouteOptions, Field(description="Selected option")]
    reason: Annotated[str, Field(description="Reason for the decision")]

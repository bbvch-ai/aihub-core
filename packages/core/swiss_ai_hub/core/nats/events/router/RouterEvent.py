from typing import Annotated, ClassVar

from pydantic import Field

from swiss_ai_hub.core.i18n.LocaleString import LocaleString
from swiss_ai_hub.core.nats.events.ControlAndDisplayEvent import ControlAndDisplayEvent
from swiss_ai_hub.core.nats.events.router.RouteOptions import RouteOptions


class RouterEvent(ControlAndDisplayEvent):
    """
    A RouterEvent marks a point where an LLM decided which way to go in the workflow.
    """

    _display_name: ClassVar[LocaleString] = LocaleString.from_i18n_path("lib.events.router_event.name")
    _display_description: ClassVar[LocaleString] = LocaleString.from_i18n_path("lib.events.router_event.description")

    routes: Annotated[list[RouteOptions], Field(..., description="List of options")]
    selected_option: Annotated[RouteOptions, Field(description="Selected option")]
    reason: Annotated[str, Field(description="Reason for the decision")]

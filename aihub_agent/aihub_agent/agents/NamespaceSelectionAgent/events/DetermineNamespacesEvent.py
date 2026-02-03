"""Event triggering LLM namespace determination step."""

from typing import ClassVar

from aihub_lib.nats.events.control.ControlEvent import ControlEvent

from aihub_agent.i18n.AgentLocaleString import AgentLocaleString


class DetermineNamespacesEvent(ControlEvent):
    """Internal event that triggers the LLM namespace determination step.

    This event is emitted to enter or re-enter the namespace determination loop.
    The conversation history and available namespaces are stored in RunContext,
    not in this event, to keep the event lightweight.
    """

    _display_name: ClassVar = AgentLocaleString.from_i18n_path("agent.events.determine_namespaces.name")
    _display_description: ClassVar = AgentLocaleString.from_i18n_path("agent.events.determine_namespaces.description")

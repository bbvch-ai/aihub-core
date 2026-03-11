from typing import Annotated, ClassVar

from pydantic import Field

from swiss_ai_hub.core.events.agent.display.display_event import DisplayEvent
from swiss_ai_hub.core.i18n.locale_string import LocaleString


class ThoughtEvent(DisplayEvent):
    """
    An event representing the system or agent's internal reasoning process, often displayed as
    a "thought" or debug info stream. These "thoughts" provide insight into how the agent arrives
    at decisions, though they don't influence control flow (since it's a DisplayEvent).

    ### Why ThoughtEvent?
    While `ControlEvent` affects workflow logic, `ThoughtEvent` provides transparency,
    revealing the reasoning paths taken by the agent. Useful for debugging, auditing, or
    explaining the agent’s behavior to end-users (e.g., "chain-of-thought" explanations).
    """

    _display_name: ClassVar[LocaleString] = LocaleString.from_i18n_path("lib.events.thought_event.name")
    _display_description: ClassVar[LocaleString] = LocaleString.from_i18n_path("lib.events.thought_event.description")
    reasoning_content: Annotated[
        str | None,
        Field(
            description="The textual representation of the agent’s internal reasoning at a particular point in time."
        ),
    ] = None

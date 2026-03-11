from typing import ClassVar

from swiss_ai_hub.core.events.agent.guard.GuardAcceptEvent import GuardAcceptEvent
from swiss_ai_hub.core.i18n.LocaleString import LocaleString


class AgentSuitabilityAcceptEvent(GuardAcceptEvent):
    """
    Event indicating that the agent suitability guard accepted the request.

    This event is triggered when the agent suitability guard determines that
    the user query matches the agent's capabilities and description.
    It signifies that this agent is appropriate for handling the user's request.
    """

    _display_name: ClassVar[LocaleString] = LocaleString.from_i18n_path(
        "lib.events.agent_suitability_accept_event.name"
    )
    _display_description: ClassVar[LocaleString] = LocaleString.from_i18n_path(
        "lib.events.agent_suitability_accept_event.description"
    )

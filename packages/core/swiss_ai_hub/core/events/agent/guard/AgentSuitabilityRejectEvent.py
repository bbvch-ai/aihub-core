from typing import ClassVar

from swiss_ai_hub.core.events.agent.guard.GuardRejectionEvent import GuardRejectionEvent
from swiss_ai_hub.core.i18n.LocaleString import LocaleString


class AgentSuitabilityRejectEvent(GuardRejectionEvent):
    """
    Event indicating that the agent suitability guard rejected the request.

    This event is triggered when the agent suitability guard determines that
    the user query does not match the agent's capabilities and description.
    It signifies that this agent is not appropriate for handling the user's request
    and the request should be routed to a different agent.
    """

    _display_name: ClassVar[LocaleString] = LocaleString.from_i18n_path(
        "lib.events.agent_suitability_reject_event.name"
    )
    _display_description: ClassVar[LocaleString] = LocaleString.from_i18n_path(
        "lib.events.agent_suitability_reject_event.description"
    )

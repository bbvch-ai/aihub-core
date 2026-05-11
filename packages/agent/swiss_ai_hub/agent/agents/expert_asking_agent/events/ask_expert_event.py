from typing import Annotated

from pydantic import Field
from swiss_ai_hub.core.auth import UserIdentity
from swiss_ai_hub.core.events.agent import ControlEvent
from swiss_ai_hub.core.i18n import LocaleHandler


class AskExpertEvent(ControlEvent):
    """Event representing a request to a group of experts for assistance by a user."""

    question_to_expert: Annotated[str, Field(..., description="The question to ask the expert")]
    locale: Annotated[
        str | None,
        Field(
            description="The user's locale, defaults to a system-wide default locale, "
            "guiding language or regional adaptations.",
        ),
    ] = LocaleHandler.DEFAULT_LOCALE
    user: Annotated[UserIdentity, Field(description="User who sent the message")]
    org_memory_namespace: Annotated[
        str | None,
        Field(
            description=(
                "Optional namespace for organization-memory writes. "
                "When set, overrides the agent profile's configured tenant_namespace for this run."
            ),
        ),
    ] = None

from typing import Annotated

from pydantic import Field
from swiss_ai_hub.core.auth.identity.UserIdentity import UserIdentity
from swiss_ai_hub.core.i18n.LocaleHandler import LocaleHandler
from swiss_ai_hub.core.nats.events.control.ControlEvent import ControlEvent


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

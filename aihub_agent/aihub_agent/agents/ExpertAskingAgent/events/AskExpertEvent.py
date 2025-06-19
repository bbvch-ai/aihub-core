from typing import Annotated, Optional

from aihub_lib.auth.identity.UserIdentity import UserIdentity
from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.nats.events import ControlEvent
from pydantic import Field


class AskExpertEvent(ControlEvent):
    """Event representing a request to a group of experts for assistance by a user."""

    question_to_expert: Annotated[str, Field(..., description="The question to ask the expert")]
    locale: Optional[str] = Field(
        LocaleHandler.DEFAULT_LOCALE,
        description="The user’s locale, defaults to a system-wide default locale, guiding language or regional adaptations.",
    )
    user: UserIdentity = Field(..., description="User who sent the message")

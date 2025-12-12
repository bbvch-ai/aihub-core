from typing import Annotated

from aihub_lib.auth.identity.UserIdentity import UserIdentity
from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.nats.events import ControlEvent
from aihub_lib.persistence.insight import InsightCallerCredentials
from pydantic import Field


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
    write_insight_namespace: Annotated[
        str | None,
        Field(description="Namespace where new insights from expert answers will be stored."),
    ] = None
    write_insight_credentials: Annotated[
        InsightCallerCredentials | None,
        Field(description="Caller credentials (agent_class, agent_id) for insight creation."),
    ] = None

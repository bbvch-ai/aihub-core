from typing import Annotated

from pydantic import Field

from swiss_ai_hub.core.auth.identity.UserIdentity import UserIdentity
from swiss_ai_hub.core.events.process.work.WorkEvent import WorkEvent


class ProgramWorkEvent(WorkEvent):
    """
    WIP
    """

    submitted_by: Annotated[UserIdentity | None, Field(description="The user who submitted the form.")] = None

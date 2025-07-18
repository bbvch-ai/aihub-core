from typing import Annotated

from pydantic import Field

from aihub_lib.auth.identity.UserIdentity import UserIdentity
from aihub_lib.nats.events.work.WorkEvent import WorkEvent


class ProgramWorkEvent(WorkEvent):
    """
    WIP
    """

    submitted_by: Annotated[UserIdentity | None, Field(description="The user who submitted the form.")] = None

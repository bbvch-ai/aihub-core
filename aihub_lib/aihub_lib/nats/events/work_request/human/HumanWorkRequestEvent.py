from typing import Annotated

from pydantic import Field

from aihub_lib.nats.events.work_request.WorkRequestEvent import WorkRequestEvent


class HumanWorkRequestEvent(WorkRequestEvent):
    """
    WIP
    """

    users: Annotated[list[str] | None, Field(description="The list of users.")] = None

from typing import List, Annotated, Optional

from pydantic import Field

from aihub_lib.nats.events.work_request.WorkRequestEvent import WorkRequestEvent


class HumanWorkRequestEvent(WorkRequestEvent):
    users: Annotated[Optional[List[str]], Field(description="The list of users.")] = None

from typing import Annotated

from aihub_lib.nats.events.work.human.HumanWorkEvent import HumanWorkEvent
from pydantic import Field

from aihub_process.delegators.AbstractProcessEntity import BaseProcessEntity


class Human(BaseProcessEntity):
    """
    WIP!
    """

    class In(BaseProcessEntity.In):
        route: str
        method: str = "POST"
        start_form: HumanWorkEvent | None = None

    class Out(BaseProcessEntity.Out):
        users: Annotated[list[str], Field(description="The list of users.")]

from typing import List, Annotated

from pydantic import Field

from aihub_lib.persistence.process.HumanProcessStepInstanceEntity import HumanIn as DBHumanIn, HumanOut as DBHumanOut
from aihub_process.delegators.AbstractProcessEntity import BaseProcessEntity


class Human(BaseProcessEntity):
    class In(BaseProcessEntity.In):
        route: str
        method: str = "POST"

    class Out(BaseProcessEntity.Out):
        users: Annotated[List[str], Field(description="The list of users.")]


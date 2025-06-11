from typing import Annotated, List

from pydantic import Field

from aihub_process.delegators.AbstractProcessEntity import BaseProcessEntity


class Human(BaseProcessEntity):
    class In(BaseProcessEntity.In):
        route: str
        method: str = "POST"

    class Out(BaseProcessEntity.Out):
        users: Annotated[List[str], Field(description="The list of users.")]

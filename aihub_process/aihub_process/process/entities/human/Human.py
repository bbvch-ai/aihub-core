from typing import List, Annotated, Type, TYPE_CHECKING

from pydantic import Field

from aihub_process.process.entities.BaseProcessEntity import BaseProcessEntity
from aihub_lib.persistence.process.HumanProcessStepInstanceEntity import HumanIn as DBHumanIn, HumanProcessStepInstanceEntity, HumanOut as DBHumanOut
from aihub_process.process.io.human.HumanWorkRequest import HumanWorkRequest

if TYPE_CHECKING:
    from aihub_process.dispatchers.Dispatcher import ProcessDispatcher

class Human(BaseProcessEntity):
    class In(BaseProcessEntity.In):
        route: str
        method: str = "POST"

        def to_persisted(self) -> DBHumanIn:
            return DBHumanIn(route=self.route, method=self.method)

    class Out(BaseProcessEntity.Out):
        users: Annotated[List[str], Field(description="The list of users.")]

        def to_persisted(self) -> DBHumanOut:
            return DBHumanOut(users=self.users)

        async def delegate(self, dispatcher: 'ProcessDispatcher', process_instance_id: str, db_step_doc: HumanProcessStepInstanceEntity, work_request_obj: HumanWorkRequest) -> None:
            await dispatcher._delegate_to_human(process_instance_id, db_step_doc, work_request_obj)

        def get_step_doc_type(self) -> Type[HumanProcessStepInstanceEntity]:
            return HumanProcessStepInstanceEntity
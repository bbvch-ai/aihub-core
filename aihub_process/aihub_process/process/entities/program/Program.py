from typing import Type, TYPE_CHECKING

from aihub_process.process.entities.BaseProcessEntity import BaseProcessEntity
from aihub_lib.persistence.process.ProgramProcessStepInstanceEntity import ProgramIn as DBProgramIn, ProgramProcessStepInstanceEntity, ProgramOut as DBProgramOut
from aihub_process.process.io.program.ProgramWorkRequest import ProgramWorkRequest

if TYPE_CHECKING:
    from aihub_process.dispatchers.Dispatcher import ProcessDispatcher

class Program(BaseProcessEntity):
    class In(BaseProcessEntity.In):
        route: str
        method: str = "POST"

        def to_persisted(self) -> DBProgramIn:
            return DBProgramIn(route=self.route, method=self.method)

    class Out(BaseProcessEntity.Out):
        endpoint: str
        method: str = "POST"

        def to_persisted(self) -> DBProgramOut:
            return DBProgramOut(endpoint=self.endpoint, method=self.method)

        async def delegate(self, dispatcher: 'ProcessDispatcher', process_instance_id: str, db_step_doc: ProgramProcessStepInstanceEntity, work_request_obj: ProgramWorkRequest) -> None:
            await dispatcher._delegate_to_program(process_instance_id, db_step_doc, work_request_obj)

        def get_step_doc_type(self) -> Type[ProgramProcessStepInstanceEntity]:
            return ProgramProcessStepInstanceEntity
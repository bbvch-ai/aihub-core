from typing import Type, TYPE_CHECKING

from pydantic import BaseModel

from aihub_process.process.entities.BaseProcessEntity import BaseProcessEntity
from aihub_lib.persistence.process.ProcessStepInstanceEntity import TerminalOut as DBTerminalOut, \
    ProcessStepInstanceEntity

if TYPE_CHECKING:
    from aihub_process.dispatchers.Dispatcher import ProcessDispatcher

class Terminal(BaseProcessEntity):
    class Out(BaseProcessEntity.Out):
        def to_persisted(self) -> DBTerminalOut:
            from aihub_lib.persistence.process.ProcessStepInstanceEntity import TerminalOut as DBTerminalOut
            return DBTerminalOut()

        async def delegate(self, dispatcher: 'ProcessDispatcher', process_instance_id: str, db_step_doc: ProcessStepInstanceEntity, work_request_obj: BaseModel) -> None:
            # No actual delegation, step is already marked completed by dispatcher
            pass

        def get_step_doc_type(self) -> Type['ProcessStepInstanceEntity']:
            from aihub_lib.persistence.process.ProcessStepInstanceEntity import ProcessStepInstanceEntity
            return ProcessStepInstanceEntity # Use base type for terminal


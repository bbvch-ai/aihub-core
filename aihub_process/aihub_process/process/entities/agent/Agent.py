from aihub_process.process.entities.BaseProcessEntity import BaseProcessEntity

from aihub_process.process.io.agent.AgentWorkRequest import AgentWorkRequest
from aihub_lib.persistence.process.AgentProcessStepInstanceEntity import AgentIn as DBAgentIn, AgentProcessStepInstanceEntity, AgentOut as DBAgentOut

from typing import Type, TYPE_CHECKING

if TYPE_CHECKING:
    from aihub_process.dispatchers.Dispatcher import ProcessDispatcher

class Agent(BaseProcessEntity):
    class In(BaseProcessEntity.In):
        agent_class: str
        agent_id: str

        def to_persisted(self) -> DBAgentIn:
            return DBAgentIn(agent_class=self.agent_class, agent_id=self.agent_id)

    class Out(BaseProcessEntity.Out):
        agent_class: str
        agent_id: str

        def to_persisted(self) -> DBAgentOut:
            return DBAgentOut(agent_class=self.agent_class, agent_id=self.agent_id)

        async def delegate(self, dispatcher: 'ProcessDispatcher', process_instance_id: str, db_step_doc: AgentProcessStepInstanceEntity, work_request_obj: AgentWorkRequest) -> None:
            await dispatcher._delegate_to_agent(process_instance_id, db_step_doc, work_request_obj)

        def get_step_doc_type(self) -> Type[AgentProcessStepInstanceEntity]:
            return AgentProcessStepInstanceEntity
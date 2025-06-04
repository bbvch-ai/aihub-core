from aihub_process.process.entities.BaseProcessEntity import BaseProcessEntity

from aihub_process.process.io.agent.AgentWorkRequest import AgentWorkRequest
from aihub_lib.persistence.process.AgentProcessStepInstanceEntity import AgentIn as DBAgentIn, AgentProcessStepInstanceEntity, AgentOut as DBAgentOut

from typing import Type, TYPE_CHECKING

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

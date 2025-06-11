from aihub_lib.persistence.process.AgentProcessStepInstanceEntity import AgentIn as DBAgentIn, AgentOut as DBAgentOut
from aihub_process.delegators.AbstractProcessEntity import BaseProcessEntity


class Agent(BaseProcessEntity):
    class In(BaseProcessEntity.In):
        agent_class: str
        agent_id: str

    class Out(BaseProcessEntity.Out):
        agent_class: str
        agent_id: str

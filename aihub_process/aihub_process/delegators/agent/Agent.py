from aihub_process.delegators.AbstractProcessEntity import BaseProcessEntity


class Agent(BaseProcessEntity):
    class In(BaseProcessEntity.In):
        agent_class: str
        agent_id: str

    class Out(BaseProcessEntity.Out):
        agent_class: str
        agent_id: str

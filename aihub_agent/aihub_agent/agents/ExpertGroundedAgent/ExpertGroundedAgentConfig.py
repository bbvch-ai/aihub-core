from aihub_lib.agents.AgentConfig import AgentConfig
from aihub_lib.generative_ai.resources.models.llm.LLMConfig import LLMConfig


class ExpertGroundedAgentConfig(AgentConfig):
    llm: LLMConfig
    expert_asking_agent_class: str
    expert_asking_agent_id: str

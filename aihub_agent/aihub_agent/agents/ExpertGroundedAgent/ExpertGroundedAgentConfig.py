from aihub_lib.agents.AgentConfig import AgentConfig
from aihub_lib.generative_ai.resources.models.llm.chat.ChatLLMConfig import ChatLLMConfig


class ExpertGroundedAgentConfig(AgentConfig):
    llm: ChatLLMConfig
    expert_asking_agent_class: str
    expert_asking_agent_id: str

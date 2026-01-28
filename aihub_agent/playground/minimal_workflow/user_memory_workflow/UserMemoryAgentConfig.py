from aihub_lib.agents.AgentConfig import AgentConfig
from aihub_lib.generative_ai.resources.models.llm.LLMConfig import LLMConfig


class UserMemoryAgentConfig(AgentConfig):
    llm: LLMConfig

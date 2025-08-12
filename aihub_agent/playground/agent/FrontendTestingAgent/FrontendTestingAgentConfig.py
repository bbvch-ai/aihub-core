from aihub_lib.agents.AgentConfig import AgentConfig
from aihub_lib.generative_ai.resources.models.llm.LLMConfig import LLMParameter, LLMConfig


class FrontendTestingAgentConfig(AgentConfig):
    llm: LLMConfig

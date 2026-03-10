from swiss_ai_hub.core.agents.AgentConfig import AgentConfig
from swiss_ai_hub.core.generative_ai.resources.models.llm.LLMConfig import LLMConfig


class UserMemoryAgentConfig(AgentConfig):
    llm: LLMConfig

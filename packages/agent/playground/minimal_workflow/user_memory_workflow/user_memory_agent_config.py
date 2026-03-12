from swiss_ai_hub.core.agents import AgentConfig
from swiss_ai_hub.core.generative_ai import LLMConfig


class UserMemoryAgentConfig(AgentConfig):
    llm: LLMConfig

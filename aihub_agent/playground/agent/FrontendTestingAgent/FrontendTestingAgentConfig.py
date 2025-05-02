from aihub_lib.agents.AgentConfig import AgentConfig
from aihub_lib.generative_ai.resources.models.llm.chat.ChatLLMConfig import ChatLLMConfig


class FrontendTestingAgentConfig(AgentConfig):
    llm: ChatLLMConfig

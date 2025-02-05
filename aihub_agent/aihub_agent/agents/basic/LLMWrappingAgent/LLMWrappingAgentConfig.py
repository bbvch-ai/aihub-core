from aihub_lib.agents.AgentConfig import AgentConfig
from aihub_lib.generative_ai.resources.models.chat.azure.AzureOpenAILLMConfig import AzureOpenAILLMConfig


class LLMWrappingAgentConfig(AgentConfig):
    llm: AzureOpenAILLMConfig

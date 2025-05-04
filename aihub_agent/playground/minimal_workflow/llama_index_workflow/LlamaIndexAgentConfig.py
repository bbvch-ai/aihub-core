from aihub_lib.agents.AgentConfig import AgentConfig
from aihub_lib.generative_ai.resources.models.llm.chat.azure.AzureOpenAILLMConfig import (
    AzureOpenAILLMConfig,
)
from aihub_lib.generative_ai.resources.models.llm.chat.openai_like.OpenaiLikeLLMConfig import OpenaiLikeLLMConfig


class LlamaIndexAgentConfig(AgentConfig):
    llm: OpenaiLikeLLMConfig | AzureOpenAILLMConfig

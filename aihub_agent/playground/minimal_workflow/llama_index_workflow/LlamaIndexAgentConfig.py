from aihub_lib.agents.AgentConfig import AgentConfig
from aihub_lib.generative_ai.resources.models.chat.azure.AzureOpenAILLMConfig import (
    AzureOpenAILLMConfig,
)
from aihub_lib.generative_ai.resources.models.chat.self_hosted.SelfHostedLLMConfig import SelfHostedLLMConfig


class LlamaIndexAgentConfig(AgentConfig):
    llm: SelfHostedLLMConfig | AzureOpenAILLMConfig

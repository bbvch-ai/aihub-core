from aihub_lib.generative_ai.agent.AgentConfig import AgentConfig
from aihub_lib.generative_ai.llms.models.chat.azure.AzureOpenAILLMConfig import (
    AzureOpenAILLMConfig,
)
from aihub_lib.generative_ai.llms.models.chat.self_hosted.SelfHostedLLMConfig import SelfHostedLLMConfig


class LlamaIndexAgentConfig(AgentConfig):
    llm: SelfHostedLLMConfig | AzureOpenAILLMConfig

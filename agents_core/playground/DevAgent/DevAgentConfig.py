from lib_core.generative_ai.agent.AgentConfig import AgentConfig
from lib_core.generative_ai.llms.models.chat.azure.AzureOpenAILLMConfig import AzureOpenAILLMConfig


class DevAgentConfig(AgentConfig):
    llm: AzureOpenAILLMConfig
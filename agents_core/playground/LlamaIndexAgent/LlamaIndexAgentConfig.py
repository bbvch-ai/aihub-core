from agents_core.agents.abstract.AgentConfig import AgentConfig, StepConfig
from lib_core.generative_ai.llms.models.chat.azure.AzureOpenAILLMEntity import AzureOpenAILLMConfig


class LlamaIndexAgentConfig(AgentConfig):
    llm: AzureOpenAILLMConfig
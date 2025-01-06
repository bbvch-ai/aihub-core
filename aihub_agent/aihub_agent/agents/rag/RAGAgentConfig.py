from aihub_lib.generative_ai.agent.AgentConfig import AgentConfig
from aihub_lib.generative_ai.llms.models.chat.azure.AzureOpenAILLMConfig import (
    AzureOpenAILLMConfig,
)
from aihub_agent.agents.rag.RetrieverStepConfig import RetrieverStepConfig


class RAGAgentConfig(AgentConfig):
    llm: AzureOpenAILLMConfig
    retriever_step_config: RetrieverStepConfig

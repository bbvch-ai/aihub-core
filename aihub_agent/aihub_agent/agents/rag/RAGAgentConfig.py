from aihub_lib.generative_ai.agent.AgentConfig import AgentConfig
from aihub_lib.generative_ai.llms.models.chat.azure.AzureOpenAILLMConfig import (
    AzureOpenAILLMConfig,
)
from aihub_agent.agents.rag.RetrieveStepConfig import RetrieveStepConfig


class RAGAgentConfig(AgentConfig):
    llm: AzureOpenAILLMConfig
    retrieve_step_config: RetrieveStepConfig

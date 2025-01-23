from aihub_lib.generative_ai.agent.AgentConfig import AgentConfig
from aihub_lib.generative_ai.llms.models.chat.azure.AzureOpenAILLMConfig import AzureOpenAILLMConfig
from aihub_lib.generative_ai.llms.models.chat.self_hosted.SelfHostedLLMConfig import SelfHostedLLMConfig
from aihub_lib.i18n.LocaleString import LocaleString
from pydantic import Field

from aihub_agent.agents.rag.Configs.RetrieveStepConfig import RetrieveStepConfig


class MultiHopRAGAgentConfig(AgentConfig):
    """
    Configuration for a RAGAgent, specifying the LLM, retrieval parameters, and prompts used to generate responses.
    """

    llm: AzureOpenAILLMConfig|SelfHostedLLMConfig = Field(..., description="The LLM configuration for the agent.")
    retrieve_step_config: RetrieveStepConfig = Field(..., description="The configuration for the retrieval step.")
    number_of_input_tokens: int = Field(
        ..., description="Maximum tokens allowed in input to manage context size or cost."
    )
    hops: int = Field(..., description="The number of hops to use.")
    decompose_chat_history_prompt: LocaleString = Field(
        ..., description="Prompt template for decomposition of chat history into multiple questions."
    )
    context_prompt: LocaleString = Field(
        ..., description="Prompt template for providing context (e.g., retrieved documents) to the LLM."
    )

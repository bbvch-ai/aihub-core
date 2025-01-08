from pydantic import Field

from aihub_lib.generative_ai.agent.AgentConfig import AgentConfig
from aihub_lib.generative_ai.llms.models.chat.azure.AzureOpenAILLMConfig import (
    AzureOpenAILLMConfig,
)
from aihub_agent.agents.rag.Configs.RetrieveStepConfig import RetrieveStepConfig
from aihub_lib.i18n.LocaleString import LocaleString


class RAGAgentConfig(AgentConfig):
    llm: AzureOpenAILLMConfig
    retrieve_step_config: RetrieveStepConfig
    number_of_input_tokens: int = Field(
        default=2048,
        description="Maximum umber of input tokens to use for context.",
    )
    tokenizer_for_model: str = Field(
        default="gpt-4o",
        description="Tokenizer to use for the model.",
    )
    condense_question_prompt: LocaleString
    context_prompt: LocaleString

from typing import List, Optional

from aihub_lib.agents.AgentConfig import AgentConfig
from aihub_lib.generative_ai.prompting.few_shot.FewShotGuardExample import FewShotGuardExample
from aihub_lib.generative_ai.resources.models.llm.chat.ChatLLMConfig import ChatLLMConfig
from aihub_lib.i18n.LocaleString import LocaleString
from pydantic import Field

from aihub_agent.agents.rag.configs.RetrieveStepConfig import RetrieveStepConfig


class RAGAgentConfig(AgentConfig):
    """
    Configuration for a RAGAgent, specifying the LLM, retrieval parameters, and prompts used to generate responses.
    """

    llm: ChatLLMConfig = Field(..., description="The LLM configuration for the agent.")
    retrieve_step_config: RetrieveStepConfig = Field(..., description="The configuration for the retrieval step.")
    number_of_input_tokens: int = Field(
        ..., description="Maximum tokens allowed in input to manage context size or cost."
    )
    condense_question_prompt: Optional[LocaleString] = Field(
        None, description="Prompt template for transforming a user query into a standalone question."
    )
    context_prompt: Optional[LocaleString] = Field(
        None, description="Prompt template for providing context (e.g., retrieved documents) to the LLM."
    )
    few_shot_guard_examples: List[FewShotGuardExample] = Field(
        default_factory=list, description="Examples for the few-shot guard to define which user requests are accepted."
    )
    check_context_sufficiency: Optional[bool] = Field(
        default=True,
        description="Whether or not to check if the retrieved context is sufficient for generating a response.",
    )

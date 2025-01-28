from aihub_lib.generative_ai.agent.AgentConfig import AgentConfig
from aihub_lib.generative_ai.llms.models.chat.azure.AzureOpenAILLMConfig import AzureOpenAILLMConfig
from aihub_lib.i18n.LocaleString import LocaleString
from pydantic import Field

from aihub_agent.steps.prompting.few_shot_step.FewShotStepConfig import FewShotStepConfig


class FewShotAgentConfig(AgentConfig):
    llm: AzureOpenAILLMConfig
    few_shot: FewShotStepConfig
    condense_question_prompt: LocaleString = Field(
        ..., description="Prompt template for transforming a user query into a standalone question."
    )
    number_of_input_tokens: int = Field(
        ..., description="Maximum tokens allowed in input to manage context size or cost."
    )

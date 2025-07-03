from typing import Annotated

from aihub_lib.agents.AgentConfig import AgentConfig
from aihub_lib.generative_ai.resources.models.llm.chat.ChatLLMConfig import ChatLLMConfig
from aihub_lib.i18n.LocaleString import LocaleString
from pydantic import Field

from aihub_agent.steps.prompting.few_shot_step.FewShotStepConfig import FewShotStepConfig


class FewShotAgentConfig(AgentConfig):
    llm: ChatLLMConfig
    few_shot: FewShotStepConfig
    condense_question_prompt: Annotated[
        LocaleString, Field(description="Prompt template for transforming a user query into a standalone question.")
    ]
    number_of_input_tokens: Annotated[
        int, Field(description="Maximum tokens allowed in input to manage context size or cost.")
    ]

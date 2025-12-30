from typing import Annotated

from aihub_lib.agents.AgentConfig import AgentConfig
from aihub_lib.generative_ai.resources.models.llm.LLMConfig import LLMConfig
from pydantic import Field

from aihub_agent.steps.prompting.few_shot_step.FewShotStepConfig import FewShotStepConfig


class FewShotAgentConfig(AgentConfig):
    llm: LLMConfig
    few_shot: FewShotStepConfig
    number_of_input_tokens: Annotated[
        int, Field(description="Maximum tokens allowed in input to manage context size or cost.")
    ]

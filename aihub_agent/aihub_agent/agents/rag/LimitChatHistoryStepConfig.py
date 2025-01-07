from aihub_lib.generative_ai.agent.AgentConfig import StepConfig
from pydantic import Field


class LimitChatHistoryStepConfig(StepConfig):
    number_of_input_tokens: int = Field(
        default=2048,
        description="Maximum umber of input tokens to use for context.",
    )

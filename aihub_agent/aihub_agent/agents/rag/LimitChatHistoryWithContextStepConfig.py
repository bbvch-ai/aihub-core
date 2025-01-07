from aihub_lib.generative_ai.agent.AgentConfig import StepConfig
from pydantic import Field


class LimitChatHistoryWithContextStepConfig(StepConfig):
    number_of_input_tokens: int = Field(
        default=2048,
        description="Maximum umber of input tokens to use for context.",
    )
    tokenizer_for_model: str = Field(
        default="gpt-4o",
        description="Tokenizer to use for the model.",
    )

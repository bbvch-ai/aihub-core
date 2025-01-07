from aihub_lib.generative_ai.agent.AgentConfig import StepConfig
from pydantic import Field


class CondenseStandaloneQuestionStepConfig(StepConfig):
    output_method: str = Field(
        ..., description="The method to output the condensed question."
    )

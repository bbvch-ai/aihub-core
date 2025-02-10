from pydantic import BaseModel, Field

from aihub_lib.generative_ai.processors.VectorPrevNextPostProcessor import ModeOptions


class RetrievePrevNextConfig(BaseModel):
    num_nodes: int = Field(..., description="The number of previous and next nodes to retrieve.")
    mode: ModeOptions = Field(..., description="The mode for the post-processor, can be 'previous', 'next', or 'both'.")

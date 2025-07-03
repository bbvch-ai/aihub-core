from typing import Annotated

from pydantic import BaseModel, Field

from aihub_lib.generative_ai.processors.VectorPrevNextPostProcessor import ModeOptions


class RetrievePrevNextConfig(BaseModel):
    num_nodes: Annotated[int, Field(description="The number of previous and next nodes to retrieve.")]
    mode: Annotated[
        ModeOptions, Field(description="The mode for the post-processor, can be 'previous', 'next', or 'both'.")
    ]

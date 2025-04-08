from typing import Annotated

from aihub_lib.agents.AgentConfig import AgentConfig
from aihub_lib.generative_ai.resources.models.llm.chat.ChatLLMConfig import ChatLLMConfig
from pydantic import BaseModel, Field


class Expert(BaseModel):
    name: Annotated[str, Field(..., description="Name of the expert")]
    email: Annotated[str, Field(..., description="Email of the expert")]
    expertise: Annotated[str, Field(..., description="Expertise of the expert")]


class ExpertAskingAgentConfig(AgentConfig):
    llm: ChatLLMConfig
    experts: Annotated[list[Expert], Field(..., description="List of experts to consult")]
    loop_max: Annotated[int, Field(3, description="Maximum number of loops to ask experts", gt=0)]

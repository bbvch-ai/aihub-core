from typing import Annotated

from pydantic import Field

from aihub_agent.agents.RagAgent.configs.RetrieveStepConfig import RetrieveStepConfig
from aihub_lib.agents.AgentConfig import AgentConfig


class RetrievalAgentConfig(AgentConfig):
    retrieve_step_config: Annotated[RetrieveStepConfig, Field(..., description="The configuration for the retrieval step.")]

from typing import Annotated

from aihub_lib.agents.AgentConfig import AgentConfig
from aihub_lib.i18n.LocaleString import LocaleString
from pydantic import Field

from aihub_agent.agents.RagAgent.configs.RetrieveStepConfig import RetrieveStepConfig


class RetrievalAgentConfig(AgentConfig):
    retrieve_step_config: Annotated[
        RetrieveStepConfig, Field(..., description="The configuration for the retrieval step.")
    ]
    context_prompt: Annotated[LocaleString | None, Field(description="The context prompt for the retrieval step.")] = (
        None
    )

from typing import Annotated

from aihub_lib.agents.AgentConfig import AgentConfig
from aihub_lib.generative_ai.resources.models.llm.LLMConfig import LLMConfig
from pydantic import Field


class InsightAgentConfig(AgentConfig):
    """Configuration for the InsightAgent."""

    llm: LLMConfig
    namespace: Annotated[
        str,
        Field("default", description="Namespace for organizing insights in the database"),
    ] = "default"

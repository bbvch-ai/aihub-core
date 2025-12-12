from typing import Annotated

from pydantic import Field

from aihub_lib.agents.AgentConfig import StepConfig
from aihub_lib.generative_ai.retrievers import InsightSourceConfig


class InsightRetrievalStepConfig(StepConfig):
    """
    Step configuration for insight retrieval.

    Contains settings for querying expert-provided insights from MongoDB.
    The sources list defines the default insight sources to query (can be overridden at runtime).
    """

    sources: Annotated[
        list[InsightSourceConfig],
        Field(description="List of insight sources (namespace, agent_class, agent_id) to query.", min_length=1),
    ]

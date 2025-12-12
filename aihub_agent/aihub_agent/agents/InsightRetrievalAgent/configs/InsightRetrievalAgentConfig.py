from typing import Annotated

from aihub_lib.agents.AgentConfig import AgentConfig
from aihub_lib.agents.step_configs import InsightRetrievalStepConfig
from aihub_lib.i18n.LocaleString import LocaleString
from pydantic import Field


class InsightRetrievalAgentConfig(AgentConfig):
    """
    Configuration for the InsightRetrievalAgent.

    Contains all settings needed for insight (MongoDB) retrieval:
    - Retrieval step config with default insight sources
    - Context prompt template

    Note: No reranking is applied for insights as they are curated knowledge.
    """

    retrieval: Annotated[
        InsightRetrievalStepConfig,
        Field(description="Insight retrieval step configuration with default sources."),
    ]

    context_prompt: Annotated[
        LocaleString | None,
        Field(description="Prompt template for combining retrieved nodes into context."),
    ] = None

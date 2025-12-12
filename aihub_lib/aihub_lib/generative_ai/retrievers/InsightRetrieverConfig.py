from typing import Annotated, Literal

from pydantic import Field

from aihub_lib.generative_ai.retrievers.BaseRetrieverConfig import BaseRetrieverConfig, RetrieverType


class InsightRetrieverConfig(BaseRetrieverConfig):
    """Configuration for retrieving insights from MongoDB."""

    retriever_type: Literal[RetrieverType.INSIGHT] = RetrieverType.INSIGHT

    namespace: Annotated[str, Field(description="The namespace to filter insights by.")]
    agent_class: Annotated[str, Field(description="The agent class to filter insights by.")]
    agent_id: Annotated[str, Field(description="The agent ID to filter insights by.")]

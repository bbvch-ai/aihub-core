from typing import Annotated, Literal

from pydantic import Field

from aihub_lib.generative_ai.retrievers.BaseRetrieverConfig import BaseRetrieverConfig, RetrieverType


class InsightRetrieverConfig(BaseRetrieverConfig):
    """Configuration for retrieving insights from MongoDB.

    Supports dynamic namespace filtering via index_namespaces field, which can be
    set at runtime by filter_retrievers_by_namespace when used with NamespaceSelectionAgent.
    """

    retriever_type: Literal[RetrieverType.INSIGHT] = RetrieverType.INSIGHT

    agent_class: Annotated[str, Field(description="The agent class to filter insights by.")]
    agent_id: Annotated[str, Field(description="The agent ID to filter insights by.")]
    index_namespaces: Annotated[
        list[str],
        Field(
            description="Namespaces to filter insights by (compound format 'bucket/namespace'). "
            "Empty list means retrieve all insights for the agent.",
        ),
    ] = []

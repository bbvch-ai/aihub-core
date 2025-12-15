from typing import Annotated

from pydantic import Field

from aihub_agent.agents.configs.AgentReference import AgentReference


class KnowledgeRetrievalAgentReference(AgentReference):
    """
    Reference to a KnowledgeRetrievalAgent with bucket association.

    Used in RAG agent configs to specify which bucket a knowledge retrieval agent handles.
    This enables bucket->namespace selection mapping from NamespaceSelectionAgent.
    """

    bucket_name: Annotated[
        str,
        Field(description="The bucket this knowledge retrieval agent handles."),
    ]

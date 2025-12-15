from typing import Annotated

from aihub_lib.nats.events.user import UserMessageEvent
from aihub_lib.persistence.insight import InsightCallerCredentials
from pydantic import Field

from aihub_agent.agents.RagAgent.events.BucketNamespaceSelection import BucketNamespaceSelection


class RAGUserMessageEvent(UserMessageEvent):
    """
    Start event for RAG agents with optional namespace selections.

    Extends UserMessageEvent with optional fields that allow callers to
    customize retrieval at runtime via bucket-based namespace selection.

    Example:
        RAGUserMessageEvent(
            messages=[...],
            bucket_namespace_selections=[
                BucketNamespaceSelection(bucket_name="knowledge", namespaces=["hr-policies"]),
            ]
        )

    The RAG agent maps bucket_name to the appropriate KnowledgeRetrievalAgent
    via KnowledgeRetrievalAgentReference.bucket_name in its config.
    """

    insight_caller_credentials: Annotated[
        InsightCallerCredentials | None,
        Field(description="Optional caller credentials (agent_class, agent_id) for insight creation."),
    ] = None

    bucket_namespace_selections: Annotated[
        list[BucketNamespaceSelection] | None,
        Field(
            description="Namespace selections per bucket. "
            "RAG agent maps bucket to retrieval agent via KnowledgeRetrievalAgentReference.bucket_name."
        ),
    ] = None

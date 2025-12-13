from typing import Annotated

from aihub_lib.generative_ai.retrievers import RetrievalOverride
from aihub_lib.nats.events.user import UserMessageEvent
from aihub_lib.persistence.insight import InsightCallerCredentials
from pydantic import Field


class RAGUserMessageEvent(UserMessageEvent):
    """
    Start event for RAG agents with optional retrieval overrides.

    Extends UserMessageEvent with optional override fields that allow
    callers to customize retrieval at runtime.

    The `retrieval_overrides` dict maps agent_id to a type-specific override:
    - `KnowledgeRetrievalOverride(type="knowledge", namespaces=[...])`
    - `InsightRetrievalOverride(type="insight", sources=[...])`

    Example:
        RAGUserMessageEvent(
            messages=[...],
            retrieval_overrides={
                "knowledge-agent-1": KnowledgeRetrievalOverride(namespaces=["hr-policies"]),
                "insight-agent-1": InsightRetrievalOverride(sources=[...]),
            }
        )

    Priority chain:
    1. Event overrides (if provided for agent_id)
    2. Agent config (default)
    """

    retrieval_overrides: Annotated[
        dict[str, RetrievalOverride] | None,
        Field(description="Agent-specific retrieval overrides (agent_id -> type-specific override)."),
    ] = None

    insight_caller_credentials: Annotated[
        InsightCallerCredentials | None,
        Field(description="Optional caller credentials (agent_class, agent_id) for insight creation."),
    ] = None

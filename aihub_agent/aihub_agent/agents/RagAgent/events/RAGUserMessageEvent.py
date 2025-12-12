from typing import Annotated

from aihub_lib.generative_ai.retrievers import InsightSourceConfig, KnowledgeNamespaceOverride
from aihub_lib.nats.events.user import UserMessageEvent
from aihub_lib.persistence.insight import InsightCallerCredentials
from pydantic import Field


class RAGUserMessageEvent(UserMessageEvent):
    """
    Start event for RAG agents with optional retrieval overrides.

    Extends UserMessageEvent with optional override fields that allow
    callers to customize retrieval at runtime:
    - `knowledge_overrides`: Override namespaces for specific knowledge retrieval agents
    - `insight_overrides`: Override or add insight sources
    - `insight_caller_credentials`: Override caller identity for insight creation

    Priority chain:
    1. Event overrides (if provided)
    2. Agent config (default)
    """

    knowledge_overrides: Annotated[
        list[KnowledgeNamespaceOverride] | None,
        Field(description="Optional overrides for knowledge retrieval agent namespaces."),
    ] = None

    insight_overrides: Annotated[
        list[InsightSourceConfig] | None,
        Field(description="Optional overrides for insight sources."),
    ] = None

    insight_caller_credentials: Annotated[
        InsightCallerCredentials | None,
        Field(description="Optional caller credentials (agent_class, agent_id) for insight creation."),
    ] = None

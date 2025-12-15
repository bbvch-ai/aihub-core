"""Data models and fetching utilities for namespace selection."""

from typing import Annotated

from aihub_lib.generative_ai.retrievers.RetrievalOverride import KnowledgeRetrievalOverride
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events.user import UserMessageEvent
from aihub_lib.persistence.rag.datalake.entities.BucketEntity import BucketEntity
from aihub_lib.persistence.rag.datalake.entities.NamespaceEntity import NamespaceEntity
from pydantic import BaseModel, Field

from aihub_agent.agents.NamespaceSelectionAgent.configs.NamespaceSelectionAgentConfig import (
    NamespaceSelectionAgentConfig,
)
from aihub_agent.agents.RagAgent.events import RAGUserMessageEvent


class NamespaceInfo(BaseModel):
    """Information about a single namespace."""

    name: Annotated[str, Field(description="Namespace identifier")]
    display_name: Annotated[LocaleString | None, Field(default=None, description="Localized display name")]


class BucketInfo(BaseModel):
    """Information about a bucket and its namespaces."""

    bucket_name: Annotated[str, Field(description="Bucket identifier")]
    bucket_display_name: Annotated[
        LocaleString | None, Field(default=None, description="Localized bucket display name")
    ]
    namespaces: Annotated[list[NamespaceInfo], Field(description="List of namespaces in this bucket")]


# ThreadContext key for persisted namespace selections
NAMESPACE_SELECTIONS_KEY = "namespace_selections"

# RunContext keys for within-run state
AVAILABLE_NAMESPACES_KEY = "available_namespaces"
PARTIAL_SELECTIONS_KEY = "partial_selections"


async def fetch_available_namespaces(
    agent_config: NamespaceSelectionAgentConfig,
) -> dict[str, BucketInfo]:
    """Fetches namespaces for all configured buckets."""
    result: dict[str, BucketInfo] = {}

    for bucket_ref in agent_config.buckets:
        if bucket_ref.bucket_id:
            bucket = BucketEntity.get_bucket_by_id(bucket_ref.bucket_id)
        else:
            assert bucket_ref.bucket_name is not None
            bucket = BucketEntity.get_bucket_by_bucket_name(bucket_ref.bucket_name)

        bucket_id = str(bucket.id)

        namespaces = NamespaceEntity.get_namespaces_by_bucket(bucket_id)

        namespace_list = [
            NamespaceInfo(
                name=ns.namespace_name,
                display_name=ns.display_name.to_locale_string() if ns.display_name else None,
            )
            for ns in namespaces
        ]

        result[bucket_id] = BucketInfo(
            bucket_name=bucket.bucket_name,
            bucket_display_name=bucket.name.to_locale_string() if bucket.name else None,
            namespaces=namespace_list,
        )

    return result


def create_rag_event_with_overrides(
    event: UserMessageEvent,
    selections: dict[str, str],
    knowledge_retrieval_agent_id: str,
    rag_agent_class: str,
    rag_agent_id: str,
) -> tuple[RAGUserMessageEvent, dict[str, KnowledgeRetrievalOverride]]:
    """
    Creates a RAGUserMessageEvent with namespace overrides from selections.

    Returns the RAG event and the overrides dict for use with AgentInTheLoop.invoke().
    """
    namespaces = list(selections.values())
    overrides = {
        knowledge_retrieval_agent_id: KnowledgeRetrievalOverride(
            type="knowledge",
            namespaces=namespaces,
        )
    }

    rag_event = RAGUserMessageEvent(
        messages=event.messages,
        locale=event.locale,
        user=event.user,
        retrieval_overrides=overrides,
    )

    return rag_event, overrides

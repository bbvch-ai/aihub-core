"""Data models and fetching utilities for namespace selection."""

from typing import Annotated

from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events.user import UserMessageEvent
from aihub_lib.persistence.rag.datalake.entities.BucketEntity import BucketEntity
from aihub_lib.persistence.rag.datalake.entities.NamespaceEntity import NamespaceEntity
from pydantic import BaseModel, Field

from aihub_agent.agents.NamespaceSelectionAgent.configs.NamespaceSelectionAgentConfig import (
    NamespaceSelectionAgentConfig,
)
from aihub_agent.agents.RagAgent.events import BucketNamespaceSelection, RAGUserMessageEvent


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


# ThreadContext keys for persisted state
NAMESPACE_SELECTIONS_KEY = "namespace_selections"
AVAILABLE_NAMESPACES_KEY = "available_namespaces"

# RunContext key for within-run state
PARTIAL_SELECTIONS_KEY = "partial_selections"


async def fetch_available_namespaces(
    agent_config: NamespaceSelectionAgentConfig,
) -> list[BucketInfo]:
    """Fetches namespaces for all configured buckets."""
    result: list[BucketInfo] = []

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

        result.append(
            BucketInfo(
                bucket_name=bucket.bucket_name,
                bucket_display_name=bucket.name.to_locale_string() if bucket.name else None,
                namespaces=namespace_list,
            )
        )

    return result


def create_rag_event_with_bucket_selections(
    event: UserMessageEvent,
    selections: list[BucketNamespaceSelection],
) -> RAGUserMessageEvent:
    """
    Creates a RAGUserMessageEvent with bucket namespace selections.

    Args:
        event: The original user message event.
        selections: List of bucket namespace selections.

    Returns:
        RAGUserMessageEvent with bucket_namespace_selections set.
    """
    return RAGUserMessageEvent(
        messages=event.messages,
        locale=event.locale,
        user=event.user,
        bucket_namespace_selections=selections,
    )

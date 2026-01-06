"""
LLM-based namespace selection for NamespaceSelectionAgent.

Provides functionality to:
1. Fetch available namespaces from the database
2. Use LLM to select relevant namespaces based on user query
3. Parse structured LLM responses
"""

import logging
from typing import Annotated

from aihub_lib.displayers.EventDisplayer import EventDisplayer
from aihub_lib.generative_ai.resources.models.llm.LLMConfig import LLMConfig
from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events import KnowledgeSource
from aihub_lib.persistence.rag.datalake.entities.BucketEntity import BucketEntity
from aihub_lib.persistence.rag.datalake.entities.NamespaceEntity import NamespaceEntity
from llama_index.core.prompts.rich import RichPromptTemplate
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class AvailableNamespace(BaseModel):
    """Represents an available namespace with its metadata."""

    bucket_name: Annotated[str, Field(description="The bucket name")]
    bucket_id: Annotated[str, Field(description="The bucket ID")]
    namespace_name: Annotated[str, Field(description="The namespace name")]
    display_name: Annotated[str | None, Field(description="Human-readable display name")] = None
    description: Annotated[str | None, Field(description="Namespace description")] = None


class SelectedSource(BaseModel):
    """A single selected knowledge source."""

    bucket_name: Annotated[str, Field(description="The bucket name")]
    namespace_name: Annotated[str, Field(description="The namespace name")]


class LLMSelectionOutput(BaseModel):
    """Structured output from LLM for namespace selection."""

    selected_sources: Annotated[list[SelectedSource], Field(description="Selected knowledge sources (one per bucket)")]
    reasoning: Annotated[str, Field(description="Brief explanation of why these sources were selected")]


class NamespaceSelectionResult(BaseModel):
    """Result of namespace selection by the LLM."""

    selected_sources: Annotated[list[KnowledgeSource], Field(description="Selected knowledge sources")]
    reasoning: Annotated[str, Field(description="LLM's reasoning for the selection")]


def fetch_available_namespaces(allowed_bucket_names: list[str], locale: str = "en") -> list[AvailableNamespace]:
    """
    Fetch all available namespaces from allowed buckets.

    Queries the database for buckets matching the allowed names,
    then fetches all namespaces within those buckets.
    """
    available: list[AvailableNamespace] = []

    for bucket_name in allowed_bucket_names:
        try:
            bucket = BucketEntity.get_bucket_by_bucket_name(bucket_name)
            namespaces = NamespaceEntity.get_namespaces_by_bucket(str(bucket.id))

            for ns in namespaces:
                display_name = None
                description = None

                if ns.display_name:
                    display_name = getattr(ns.display_name, locale, None) or ns.display_name.en

                if ns.description:
                    description = getattr(ns.description, locale, None) or getattr(ns.description, "en", None)

                available.append(
                    AvailableNamespace(
                        bucket_name=bucket.bucket_name,
                        bucket_id=str(bucket.id),
                        namespace_name=ns.namespace_name,
                        display_name=display_name,
                        description=description,
                    )
                )
        except Exception as e:
            logger.warning(f"Failed to fetch namespaces for bucket {bucket_name}: {e}")
            continue

    return available


def _build_namespace_list_text(available_namespaces: list[AvailableNamespace]) -> str:
    """Build formatted text listing all available namespaces."""
    namespace_list = []
    for ns in available_namespaces:
        entry = f"- {ns.bucket_name}/{ns.namespace_name}"
        if ns.display_name:
            entry += f" ({ns.display_name})"
        if ns.description:
            entry += f": {ns.description}"
        namespace_list.append(entry)
    return "\n".join(namespace_list)


def _build_context_text(conversation_context: list[str] | None) -> str:
    """Build context text from conversation history."""
    if conversation_context:
        return "\n\nPrevious clarification exchanges:\n" + "\n".join(conversation_context)
    return ""


async def select_namespaces(
    user_query: str,
    available_namespaces: list[AvailableNamespace],
    llm_config: LLMConfig,
    displayer: EventDisplayer,
    t: LocaleHandler,
    selection_system_prompt: LocaleString | None = None,
    conversation_context: list[str] | None = None,
    user_correction: str | None = None,
) -> NamespaceSelectionResult:
    """
    Use LLM to select relevant namespaces based on user query.

    Uses structured prediction to get a validated response from the LLM.

    Args:
        user_query: The user's query.
        available_namespaces: List of available namespaces to select from.
        llm_config: LLM configuration.
        displayer: Event displayer for thoughts.
        t: Locale handler.
        selection_system_prompt: Optional custom system prompt (overrides default i18n prompt).
            Supports placeholders: {namespaces}, {context}.
        conversation_context: Previous clarification exchanges.
        user_correction: User's correction or preference from previous selection.
    """
    if not available_namespaces:
        return NamespaceSelectionResult(
            selected_sources=[],
            reasoning="No namespaces available",
        )

    # Include user correction in conversation context if provided
    if user_correction:
        conversation_context = conversation_context or []
        conversation_context = [f"User preference: {user_correction}"] + conversation_context

    # Build prompt - use config override if provided, else use i18n
    namespaces_text = _build_namespace_list_text(available_namespaces)
    context_text = _build_context_text(conversation_context)

    if selection_system_prompt:
        prompt_text = t.extract(selection_system_prompt).format(
            namespaces=namespaces_text,
            context=context_text,
        )
    else:
        prompt_text = t(
            "agent.namespace_selection.prompts.selection_system",
            namespaces=namespaces_text,
            context=context_text,
        )

    # Append user query
    prompt_text += f"\n\n{t('agent.namespace_selection.prompts.selection_user', query=user_query)}"

    await displayer.display_thought(t("agent.namespace_selection.thoughts.analyzing_query"))

    # Create lookup for validation
    valid_sources = {(ns.bucket_name, ns.namespace_name): ns for ns in available_namespaces}

    async with llm_config.cost_reporting_llm(displayer) as llm:
        prompt = RichPromptTemplate(prompt_text)
        llm_output = await llm.astructured_predict(LLMSelectionOutput, prompt)

    # Convert LLM output to KnowledgeSource objects, validating against available namespaces
    selected_sources: list[KnowledgeSource] = []
    for source in llm_output.selected_sources:
        key = (source.bucket_name, source.namespace_name)
        if key in valid_sources:
            ns = valid_sources[key]
            selected_sources.append(
                KnowledgeSource(
                    bucket_name=source.bucket_name,
                    namespace_name=source.namespace_name,
                    display_name=ns.display_name,
                )
            )
        else:
            logger.warning(f"LLM selected invalid source: {source.bucket_name}/{source.namespace_name}")

    return NamespaceSelectionResult(
        selected_sources=selected_sources,
        reasoning=llm_output.reasoning,
    )

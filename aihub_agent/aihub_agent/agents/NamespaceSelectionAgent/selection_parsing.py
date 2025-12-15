"""Selection parsing utilities for namespace selection."""

from typing import Annotated

from aihub_lib.displayers.EventDisplayer import EventDisplayer
from aihub_lib.i18n.LocaleHandler import LocaleHandler
from llama_index.core import PromptTemplate
from pydantic import BaseModel, Field

from aihub_agent.agents.NamespaceSelectionAgent.configs.NamespaceSelectionAgentConfig import (
    NamespaceSelectionAgentConfig,
)
from aihub_agent.agents.NamespaceSelectionAgent.namespace_data import BucketInfo
from aihub_agent.agents.NamespaceSelectionAgent.namespace_formatting import format_single_bucket_options
from aihub_agent.agents.RagAgent.events import BucketNamespaceSelection


class SelectionParseResult(BaseModel):
    """Result of parsing namespace selections from user response."""

    complete: Annotated[bool, Field(description="Whether all bucket selections are complete")]
    selections: Annotated[list[BucketNamespaceSelection], Field(description="List of bucket namespace selections")]
    follow_up: Annotated[str, Field(default="", description="Follow-up message if selections incomplete")]


class NamespaceSelectionResult(BaseModel):
    """Result of parsing a user's namespace selection response."""

    selected_namespace: Annotated[str | None, Field(description="Selected namespace name or None if unclear")]
    follow_up: Annotated[str, Field(description="Follow-up question if selection unclear")]


def namespace_selection_result_factory(
    t: LocaleHandler,
    valid_namespaces: list[str],
) -> type[NamespaceSelectionResult]:
    """
    Creates a localized NamespaceSelectionResult class with constrained namespace options.

    Uses Literal type to constrain selected_namespace to only valid options,
    improving LLM accuracy with structured output.
    """
    if valid_namespaces:
        from typing import Literal

        namespace_options = tuple(valid_namespaces)
        NamespaceLiteral = Literal[namespace_options]  # type: ignore[valid-type]
    else:
        NamespaceLiteral = str  # type: ignore[misc]

    class LocalizedNamespaceSelectionResult(NamespaceSelectionResult):
        selected_namespace: Annotated[
            NamespaceLiteral | None,
            Field(description=t("agent.namespace_selection.fields.selected_namespace")),
        ]
        follow_up: Annotated[
            str,
            Field(description=t("agent.namespace_selection.fields.follow_up")),
        ]

    LocalizedNamespaceSelectionResult.__doc__ = t("agent.namespace_selection.prompts.parse_selection")
    return LocalizedNamespaceSelectionResult


def _get_selected_bucket_names(selections: list[BucketNamespaceSelection]) -> set[str]:
    """Returns set of bucket names that have been selected."""
    return {s.bucket_name for s in selections}


async def parse_selection_response(
    user_response: str,
    available_namespaces: list[BucketInfo],
    partial_selections: list[BucketNamespaceSelection],
    agent_config: NamespaceSelectionAgentConfig,
    t: LocaleHandler,
    displayer: EventDisplayer,
) -> SelectionParseResult:
    """Parses user's selection response using structured LLM output."""
    merged_selections = list(partial_selections)
    selected_buckets = _get_selected_bucket_names(merged_selections)
    last_follow_up = ""

    for bucket_info in available_namespaces:
        if bucket_info.bucket_name in selected_buckets:
            continue

        valid_namespaces = [ns.name for ns in bucket_info.namespaces]
        formatted_options = format_single_bucket_options(bucket_info, t)

        result_class = namespace_selection_result_factory(t, valid_namespaces)
        prompt_template = PromptTemplate(t("agent.namespace_selection.prompts.parse_selection"))

        async with agent_config.llm.cost_reporting_llm(displayer) as llm:
            result: NamespaceSelectionResult = llm.structured_predict(
                result_class,
                prompt_template,
                user_response=user_response,
                namespace_options=formatted_options,
            )

        if result.selected_namespace:
            merged_selections.append(
                BucketNamespaceSelection(
                    bucket_name=bucket_info.bucket_name,
                    namespaces=[result.selected_namespace],
                )
            )
            selected_buckets.add(bucket_info.bucket_name)
        else:
            last_follow_up = result.follow_up
            break

    complete = len(merged_selections) >= len(available_namespaces)

    return SelectionParseResult(
        complete=complete,
        selections=merged_selections,
        follow_up=last_follow_up if not complete else "",
    )

"""Formatting utilities for namespace selection prompts."""

from aihub_lib.displayers.EventDisplayer import EventDisplayer
from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.i18n.LocaleString import LocaleString
from llama_index.core.base.llms.types import ChatMessage, ChatResponse, MessageRole

from aihub_agent.agents.NamespaceSelectionAgent.configs.NamespaceSelectionAgentConfig import (
    NamespaceSelectionAgentConfig,
)
from aihub_agent.agents.NamespaceSelectionAgent.namespace_data import BucketInfo


def format_single_bucket_options(
    bucket_info: BucketInfo,
    t: LocaleHandler,
) -> str:
    """Formats namespace options for a single bucket."""
    lines = []
    for ns in bucket_info.namespaces:
        ns_name = t.extract(LocaleString.model_validate(ns.display_name)) if ns.display_name else ns.name
        lines.append(f"- {ns_name} (name: {ns.name})")
    return "\n".join(lines)


def format_namespace_options(
    available_namespaces: dict[str, BucketInfo],
    t: LocaleHandler,
) -> str:
    """Formats namespace options for LLM prompt."""
    lines = []
    for bucket_id, bucket_info in available_namespaces.items():
        if bucket_info.bucket_display_name:
            bucket_name = t.extract(LocaleString.model_validate(bucket_info.bucket_display_name))
        else:
            bucket_name = bucket_info.bucket_name
        lines.append(f"\nBucket: {bucket_name} (ID: {bucket_id})")
        lines.append("Namespaces:")

        for ns in bucket_info.namespaces:
            ns_name = t.extract(LocaleString.model_validate(ns.display_name)) if ns.display_name else ns.name
            lines.append(f"  - {ns_name} (name: {ns.name})")

    return "\n".join(lines)


async def generate_selection_question(
    available_namespaces: dict[str, BucketInfo],
    user_query: str,
    agent_config: NamespaceSelectionAgentConfig,
    t: LocaleHandler,
    displayer: EventDisplayer,
) -> str:
    """Generates a friendly question asking user to select namespaces."""
    formatted_options = format_namespace_options(available_namespaces, t)

    prompt = t("agent.namespace_selection.prompts.ask_selection")
    messages = [
        ChatMessage(
            role=MessageRole.SYSTEM,
            content=prompt,
        ),
        ChatMessage(
            role=MessageRole.USER,
            content=f"User's question: {user_query}\n\nAvailable namespaces:\n{formatted_options}",
        ),
    ]

    async with agent_config.llm.cost_reporting_llm(displayer) as llm:
        response: ChatResponse = await llm.achat(messages)
        return response.message.content or t("agent.namespace_selection.messages.default_question")

"""
Topic change routing for detecting when a user's query changes topic.

Uses the LLM router pattern to determine if the current query is about a different
topic than the previous conversation, which would require re-selecting
knowledge sources.
"""

from llama_index.core.base.llms.types import ChatMessage
from llama_index.core.llms import LLM

from aihub_lib.generative_ai.routing.route_to_event_using_llm import route_to_event_using_llm
from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.nats.events.guard import TopicChangedEvent, TopicUnchangedAcceptEvent
from aihub_lib.nats.events.rag import KnowledgeSource
from aihub_lib.nats.events.router.RouteOptions import RouteOptions
from aihub_lib.nats.events.router.RouterEvent import RouterEvent

# Number of recent messages to include for topic change detection
DEFAULT_MESSAGE_HISTORY_LIMIT = 10


def _format_messages_for_prompt(messages: list[ChatMessage], limit: int = DEFAULT_MESSAGE_HISTORY_LIMIT) -> str:
    """Format the last N messages for inclusion in the topic change prompt."""
    recent_messages = messages[-limit:] if len(messages) > limit else messages
    formatted_lines = []
    for msg in recent_messages:
        role_label = msg.role.value.capitalize()
        content = msg.content if isinstance(msg.content, str) else str(msg.content)
        # Truncate very long messages
        if len(content) > 500:
            content = content[:500] + "..."
        formatted_lines.append(f"{role_label}: {content}")
    return "\n".join(formatted_lines)


async def route_topic_change(
    llm: LLM,
    t: LocaleHandler,
    current_query: str,
    current_sources: list[KnowledgeSource],
    previous_messages: list[ChatMessage] | None = None,
    message_history_limit: int = DEFAULT_MESSAGE_HISTORY_LIMIT,
) -> RouterEvent:
    """
    Route based on whether the current query represents a topic change.

    Uses LLM router pattern to determine if the user's new question is about a
    fundamentally different subject that would require searching different
    knowledge sources. Analyzes the conversation history to detect follow-up
    questions vs topic changes.

    Routes:
    - TopicUnchangedAcceptEvent: Topic is the same (including follow-ups), reuse sources
    - TopicChangedEvent: Topic has changed, need to ask user about new sources

    Args:
        llm: The LLM to use for routing decision.
        t: Locale handler for translations.
        current_query: The current user query.
        current_sources: The currently selected knowledge sources.
        previous_messages: Chat history to analyze for context and follow-ups.
        message_history_limit: Maximum number of recent messages to include.

    Returns:
        RouterEvent with the selected route (unchanged or changed).
    """
    # Build context about current sources for the prompt
    sources_text = "\n".join(f"- {s.display_name or s.namespace_name}" for s in current_sources)

    # Format conversation history for the prompt
    if previous_messages:
        conversation_context = _format_messages_for_prompt(previous_messages, message_history_limit)
    else:
        conversation_context = t("lib.prompt.routing.topic_change.no_previous_conversation")

    # Build instructions that explain the situation to the LLM
    instructions = t(
        "lib.prompt.routing.topic_change.instructions",
        current_query=current_query,
        current_sources=sources_text,
        conversation_history=conversation_context,
    )

    # Define the two possible routes
    routes = [
        RouteOptions.for_event(
            event=TopicUnchangedAcceptEvent(
                reason=t("lib.prompt.routing.topic_change.topic_unchanged_reason"),
                current_sources=current_sources,
            ),
            instructions=t("lib.prompt.routing.topic_change.unchanged_instructions"),
        ),
        RouteOptions.for_event(
            event=TopicChangedEvent(
                reasoning=t("lib.prompt.routing.topic_change.topic_changed_reason"),
                current_sources=current_sources,
            ),
            instructions=t("lib.prompt.routing.topic_change.changed_instructions"),
        ),
    ]

    return await route_to_event_using_llm(instructions, routes, llm, t)

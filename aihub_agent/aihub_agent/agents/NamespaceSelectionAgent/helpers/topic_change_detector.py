"""
Topic change detection for NamespaceSelectionAgent.

Uses LLM-based routing to detect when a user's query has changed topic
significantly, triggering user confirmation and potential re-evaluation
of namespace selection.
"""

import logging

from aihub_lib.displayers.EventDisplayer import EventDisplayer
from aihub_lib.generative_ai.routing.topic_change_router import route_topic_change
from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.nats.events import KnowledgeSource
from aihub_lib.nats.events.guard import TopicChangedEvent, TopicUnchangedAcceptEvent
from aihub_lib.nats.events.router.RouterEvent import RouterEvent
from llama_index.core.base.llms.types import ChatMessage
from llama_index.core.llms import LLM

logger = logging.getLogger(__name__)


async def detect_topic_change_with_llm(
    current_query: str,
    current_sources: list[KnowledgeSource],
    llm: LLM,
    displayer: EventDisplayer,
    t: LocaleHandler,
    previous_messages: list[ChatMessage] | None = None,
) -> RouterEvent:
    """
    Detect if the current query represents a topic change using LLM routing.

    Uses the LLM router pattern to analyze whether the user's query is about
    a fundamentally different topic than the previous conversation. Analyzes
    the conversation history to properly detect follow-up questions.

    Args:
        current_query: The current user query.
        current_sources: Currently selected knowledge sources.
        llm: LLM for topic analysis.
        displayer: For emitting display events.
        t: Locale handler for translations.
        previous_messages: Chat history to analyze for context and follow-ups.

    Returns:
        RouterEvent with selected route:
        - TopicUnchangedAcceptEvent: Topic is the same, reuse sources
        - TopicChangedEvent: Topic has changed, ask user about new sources
    """
    await displayer.display_thought(t("agent.namespace_selection.thoughts.checking_topic_change"))

    router_event = await route_topic_change(
        llm=llm,
        t=t,
        current_query=current_query,
        current_sources=current_sources,
        previous_messages=previous_messages,
    )

    selected_event = router_event.selected_option.event
    if isinstance(selected_event, TopicUnchangedAcceptEvent):
        logger.debug(f"Topic unchanged: {router_event.reason}")
        await displayer.display_thought(t("agent.namespace_selection.thoughts.topic_unchanged"))
    elif isinstance(selected_event, TopicChangedEvent):
        logger.debug(f"Topic changed: {router_event.reason}")
        await displayer.display_thought(t("agent.namespace_selection.thoughts.topic_changed"))

    return router_event

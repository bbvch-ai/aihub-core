from swiss_ai_hub.core.events.agent import (
    AnswerPostProcessedEvent,
    ContextBlockEvent,
    NotAMetaQuestionEvent,
    UserMessageEvent,
)

from swiss_ai_hub.agent.agents.agent import Agent
from swiss_ai_hub.agent.capabilities.conversation.conversation_wiring import ConversationWiring
from swiss_ai_hub.agent.self_awareness.meta_question_gate import check_passed_meta_question_gate
from swiss_ai_hub.agent.workflow.decorators.precondition import precondition


@precondition()
async def passed_meta_question_gate(
    user_message: UserMessageEvent | None = None,
    clear: NotAMetaQuestionEvent | None = None,
) -> bool:
    """Hold the spine until detection clears a chat message; a programmatic start has no message to clear."""
    return check_passed_meta_question_gate(user_message, clear)


@precondition()
async def all_context_blocks_reported(
    blueprint: type[Agent],
    blocks: list[ContextBlockEvent] | None = None,
) -> bool:
    """Every installed enricher has contributed its block, empty or not."""
    return len(blocks or []) >= ConversationWiring.count_enrichers(blueprint)


@precondition()
async def all_post_answer_hooks_reported(
    blueprint: type[Agent],
    hooks: list[AnswerPostProcessedEvent] | None = None,
) -> bool:
    """Every installed post-answer hook has reported, so nothing is left that the stop could overtake."""
    return len(hooks or []) >= ConversationWiring.count_post_answer_hooks(blueprint)

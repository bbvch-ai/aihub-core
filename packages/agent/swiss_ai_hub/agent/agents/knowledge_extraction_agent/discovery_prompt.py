from llama_index.core.base.llms.types import ChatMessage, MessageRole
from swiss_ai_hub.core.generative_ai import limit_chat_history, merge_consecutive_messages
from swiss_ai_hub.core.i18n import LocaleHandler

from swiss_ai_hub.agent.capabilities.knowledge_documents.knowledge_document_run_scope import (
    KnowledgeDocumentRunScope,
)
from swiss_ai_hub.agent.capabilities.record_extraction.extraction_history import ExtractionHistory


class DiscoveryPrompt:
    """The conversation the discovery loop works on: one leading system message with the agent's instructions and the
    run's scope, ahead of the client's own, and earlier tables replaced by a line.

    The scope is spelled out because tool descriptions cannot change per run; a model that does not know the glob
    guesses paths outside it and reads the empty results as "no such document". The model is told to search by keyword
    for what the request names exactly and to rank by meaning for what it only describes, and to judge documents, not
    rows: searches cannot settle a condition on the rows, and models that tried spent the whole loop on it.
    """

    @staticmethod
    def history(
        messages: list[ChatMessage],
        scope: KnowledgeDocumentRunScope,
        profile_instructions: str | None,
        input_budget: int,
        t: LocaleHandler,
    ) -> list[ChatMessage]:
        """The instructions, then the conversation within the input budget. The budget is the profile's own, never
        an unset limit: llama-index fills that with about 3,000 tokens and drops the turn a follow-up refers to."""
        instructions = [
            t("agent.knowledge_extraction_agent.prompt.instructions", scope=scope.describe()),
            *([profile_instructions] if profile_instructions else []),
        ]
        merged = merge_consecutive_messages(
            [
                ChatMessage(role=MessageRole.SYSTEM, content="\n\n".join(instructions)),
                *(message for message in messages if message.role == MessageRole.SYSTEM),
                *ExtractionHistory.condensed([message for message in messages if message.role != MessageRole.SYSTEM]),
            ]
        )
        head, conversation = merged[:1], merged[1:]
        return [*head, *limit_chat_history(chat_history=conversation, number_of_input_tokens=input_budget)]

from llama_index.core.base.llms.types import ChatMessage, MessageRole
from swiss_ai_hub.core.generative_ai import limit_chat_history, merge_consecutive_messages
from swiss_ai_hub.core.i18n import LocaleHandler

from swiss_ai_hub.agent.capabilities.knowledge_documents.knowledge_document_run_scope import (
    KnowledgeDocumentRunScope,
)
from swiss_ai_hub.agent.capabilities.record_extraction.extraction_history import ExtractionHistory
from swiss_ai_hub.agent.capabilities.record_extraction.pending_extraction import PendingExtraction


class DiscoveryPrompt:
    """The conversation the discovery loop works on: one leading system message with the agent's instructions and the
    run's scope, ahead of the client's own, and earlier tables replaced by a line.

    The scope is spelled out because tool descriptions cannot change per run; a model that does not know the glob
    guesses paths outside it and reads the empty results as "no such document". With semantic search the model is told
    to rank first and judge documents, not rows: lexical searches cannot settle a condition on the rows, and models
    that tried spent the whole loop on it.
    """

    @staticmethod
    def history(
        messages: list[ChatMessage],
        scope: KnowledgeDocumentRunScope,
        profile_instructions: str | None,
        number_of_input_tokens: int,
        t: LocaleHandler,
        pending: PendingExtraction | None = None,
        semantic: bool = False,
    ) -> list[ChatMessage]:
        key = "instructions_semantic" if semantic else "instructions"
        instructions = [
            t(f"agent.knowledge_extraction_agent.prompt.{key}", scope=scope.describe()),
            *([DiscoveryPrompt._pending(pending, t)] if pending else []),
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
        return [*head, *limit_chat_history(chat_history=conversation, number_of_input_tokens=number_of_input_tokens)]

    @staticmethod
    def _pending(pending: PendingExtraction, t: LocaleHandler) -> str:
        """What an earlier answer left unfinished, so the model can tell "continue" from a new request."""
        key = "agent.knowledge_extraction_agent.prompt"
        if pending.overflow_rows:
            left = t(f"{key}.pending_rows", count=len(pending.overflow_rows))
        else:
            left = t(f"{key}.pending_documents", count=pending.remaining_documents)
        return t(f"{key}.pending", criteria=pending.criteria, left=left)

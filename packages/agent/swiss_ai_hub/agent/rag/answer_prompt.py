from llama_index.core.base.llms.types import ChatMessage
from swiss_ai_hub.core.events.agent import (
    ContextInsufficientRejectEvent,
    ExpertRejectEvent,
    FewShotRejectEvent,
    RAGStartEvent,
    UserMessageEvent,
)
from swiss_ai_hub.core.i18n import LocaleHandler, LocaleString

from swiss_ai_hub.agent.capabilities.attached_files.attached_files import AttachedFiles
from swiss_ai_hub.agent.capabilities.conversation.conversation import Conversation
from swiss_ai_hub.agent.capabilities.knowledge.knowledge import Knowledge
from swiss_ai_hub.agent.capabilities.memory.memory import Memory
from swiss_ai_hub.agent.rag.citation_policy import CitationPolicy
from swiss_ai_hub.agent.rag.step_functions import do_answer_instructions


class AnswerPrompt:
    """The one prompt a RAG answer is written from, asked of the conversation capability once the outcome is known,
    so the composed context it displays is exactly what the model receives."""

    @staticmethod
    def compose(
        rejection: FewShotRejectEvent | ContextInsufficientRejectEvent | ExpertRejectEvent | None,
        context: list[ChatMessage],
        ctx: Conversation.Contextualized,
        gathered: tuple[Memory.Recalled, AttachedFiles.Contents, Knowledge.Searched],
        start_event: UserMessageEvent | RAGStartEvent,
        system_prompt: LocaleString | None,
        context_insufficient_prompt: LocaleString | None,
        t: LocaleHandler,
    ) -> Conversation.ComposeRequest:
        """The instructions lead the system head, which is never trimmed; the context comes last among the blocks,
        so when the blocks do not fit, the memories give way before the documents the answer rests on."""
        memories, files, knowledge = gathered
        instructions = do_answer_instructions(
            rejection, context_insufficient_prompt, system_prompt, t, CitationPolicy.cites_sources(start_event)
        )
        return Conversation.compose(
            [*instructions, *ctx.history], blocks=[*memories.blocks, knowledge.block, files.block, context]
        )

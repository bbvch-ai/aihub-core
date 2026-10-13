from swiss_ai_hub.core.displayers import EventDisplayer
from swiss_ai_hub.core.events.agent import LLMEvent, Message, RAGFailureReason, RAGFailureStopEvent
from swiss_ai_hub.core.i18n import LocaleHandler

from swiss_ai_hub.agent.capabilities.conversation.conversation import Conversation


class InaccessibleKnowledge:
    """The end of a RAG run whose asking user may read none of its collections."""

    @staticmethod
    async def answer(model_name: str, displayer: EventDisplayer, t: LocaleHandler) -> Conversation.CompleteRequest:
        """Say why nothing was searched, since an empty retrieval would read as "the documents do not cover this"."""
        notice = t("agent.rag_agent.messages.no_accessible_knowledge")
        await displayer.display_chunk(notice, model_name=model_name)
        answer = LLMEvent(output_messages=[Message.from_string(role="assistant", content=notice, name=model_name)])
        stop = RAGFailureStopEvent(reason=RAGFailureReason.NO_ACCESSIBLE_KNOWLEDGE, answer=notice)
        return Conversation.complete(answer=answer, stop=stop)

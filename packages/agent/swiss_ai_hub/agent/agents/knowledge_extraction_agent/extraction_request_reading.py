import logging

from llama_index.core.base.llms.types import ChatMessage, MessageRole
from llama_index.core.prompts.rich import RichPromptTemplate
from swiss_ai_hub.core.auth import UserIdentity
from swiss_ai_hub.core.displayers import EventDisplayer
from swiss_ai_hub.core.generative_ai import LLMConfig
from swiss_ai_hub.core.i18n import LocaleHandler

from swiss_ai_hub.agent.agents.knowledge_extraction_agent.extraction_request_answer import ExtractionRequestAnswer
from swiss_ai_hub.agent.agents.knowledge_extraction_agent.extraction_request_plain_answer import (
    ExtractionRequestPlainAnswer,
)
from swiss_ai_hub.agent.capabilities.knowledge_documents.knowledge_document_run_scope import (
    KnowledgeDocumentRunScope,
)

logger = logging.getLogger(__name__)

# A request reads into a handful of short fields; the cap bounds what a strict-mode stall can cost.
READING_MAX_TOKENS = 1024
# Earlier turns, so a follow-up such as "the same for 2024" reads in context; tables in them are condensed already.
CONVERSATION_CHARACTERS = 6_000


class ExtractionRequestReading:
    """Reads a chat message as a table request over the profile's whole scope, in one structured call.

    No search decides which documents are read: every document in scope is, so a document whose wording the request
    does not share is never missed. The model only states the columns, which rows to keep, the folders, files or years
    the user named, and the terms that make documents and lines likely matches, used to order and sample, never to
    leave a document out. While a sample awaits confirmation, it also tells a "yes" from a new request.
    """

    @staticmethod
    async def ask(
        history: list[ChatMessage],
        scope: KnowledgeDocumentRunScope,
        facets: list[str],
        profile_instructions: str | None,
        awaiting_sample: bool,
        llm_config: LLMConfig,
        displayer: EventDisplayer,
        user: UserIdentity | None,
        t: LocaleHandler,
    ) -> ExtractionRequestAnswer | None:
        """The request as the model reads it; None when the model gave no usable answer. A model that loops in a term
        list until its output is cut is asked once more for the request without the terms."""
        prompt = RichPromptTemplate(t("agent.knowledge_extraction_agent.prompt.read_request"))
        arguments = {
            "scope": scope.describe(),
            "facets": "\n".join(facets),
            "profile_instructions": profile_instructions or "",
            "awaiting_sample": awaiting_sample,
            "conversation": ExtractionRequestReading._conversation(history),
            "request": ExtractionRequestReading.last_request(history),
        }
        async with llm_config.cost_reporting_llm(displayer, user=user) as llm:
            deterministic = llm.model_copy(update={"temperature": 0.0, "max_tokens": READING_MAX_TOKENS})
            try:
                return await deterministic.astructured_predict(ExtractionRequestAnswer, prompt, **arguments)
            except ValueError:
                logger.warning("[knowledge-extraction] no usable request with terms, reading it without them")
            try:
                plain = await deterministic.astructured_predict(ExtractionRequestPlainAnswer, prompt, **arguments)
            except ValueError:
                logger.warning("[knowledge-extraction] the model read no usable request")
                return None
            return ExtractionRequestAnswer.without_terms(plain)

    @staticmethod
    def last_request(history: list[ChatMessage]) -> str:
        """The message being answered: the conversation's last user turn."""
        return next((message.content or "" for message in reversed(history) if message.role == MessageRole.USER), "")

    @staticmethod
    def _conversation(history: list[ChatMessage]) -> str:
        """The turns before the request, newest kept when long."""
        earlier = [message for message in history if message.role in (MessageRole.USER, MessageRole.ASSISTANT)][:-1]
        text = "\n\n".join(f"{message.role.value}: {message.content or ''}" for message in earlier)
        return text[-CONVERSATION_CHARACTERS:]

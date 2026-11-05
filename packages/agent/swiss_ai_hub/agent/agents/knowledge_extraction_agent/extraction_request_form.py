from llama_index.core.base.llms.types import ChatMessage, MessageRole
from swiss_ai_hub.core.i18n import LocaleHandler
from swiss_ai_hub.core.topic_managers import AgentTopicManager
from swiss_ai_hub.core.topics import PartialAgentTopic

from swiss_ai_hub.agent.agents.knowledge_extraction_agent.extraction_notices import ExtractionNotices
from swiss_ai_hub.agent.agents.knowledge_extraction_agent.extraction_request_answer import ExtractionRequestAnswer
from swiss_ai_hub.agent.agents.knowledge_extraction_agent.extraction_request_form_request_event import (
    ExtractionRequestFormRequestEvent,
)
from swiss_ai_hub.agent.agents.knowledge_extraction_agent.extraction_request_form_response_event import (
    ExtractionRequestFormResponseEvent,
)
from swiss_ai_hub.agent.agents.knowledge_extraction_agent.extraction_request_parts import ExtractionRequestParts
from swiss_ai_hub.agent.capabilities.record_extraction.extraction_form import ExtractionForm
from swiss_ai_hub.agent.context.run.run_context import RunContext

READING_KEY = "knowledge_extraction:request_form:reading"
CONFIRMED_KEY = "knowledge_extraction:request_form:confirmed"


class ExtractionRequestForm:
    """Asks the user to confirm where, which rows and which columns before any document is read; with discovery also
    the exact and the semantic keywords that guide the search.

    A misread part otherwise only shows in the finished table. The reading waits in the run for the answer, since the
    answer resumes the same run, and the confirmed reading stays there for the search's selection.
    """

    request = ExtractionRequestFormRequestEvent
    response = ExtractionRequestFormResponseEvent

    @classmethod
    async def ask(
        cls, reading: ExtractionRequestAnswer, folders: str, keywords: bool, run_context: RunContext, t: LocaleHandler
    ) -> ExtractionRequestFormRequestEvent:
        """`folders`: the largest folders in scope; `keywords`: whether the model searches, so the keywords matter."""
        await run_context.set(READING_KEY, reading.model_dump(mode="json"))
        parts = ExtractionRequestParts.of(reading, t, keywords).form(reading, folders, t)
        notices = ExtractionNotices.for_calculation(reading.calculation, t)
        return cls.request(
            question=ExtractionForm.text(parts, notices, t),
            questions=ExtractionForm.questions(parts, notices, t),
            topic=PartialAgentTopic(
                event_type=AgentTopicManager.CONTROL_EVENT, event_name=cls.response.event_name_from_class()
            ),
        )

    @staticmethod
    async def understood(run_context: RunContext) -> ExtractionRequestAnswer:
        return ExtractionRequestAnswer.model_validate(await run_context.get(READING_KEY))

    @staticmethod
    async def confirm(run_context: RunContext, reading: ExtractionRequestAnswer) -> None:
        await run_context.set(CONFIRMED_KEY, reading.model_dump(mode="json"))

    @staticmethod
    async def confirmed(run_context: RunContext) -> ExtractionRequestAnswer | None:
        stored = await run_context.get(CONFIRMED_KEY)
        return ExtractionRequestAnswer.model_validate(stored) if stored else None

    @staticmethod
    def answered(history: list[ChatMessage], question: str, reply: str) -> list[ChatMessage]:
        """The conversation with the form and the user's reply to it, for reading or searching once more."""
        return [
            *history,
            ChatMessage(role=MessageRole.ASSISTANT, content=question),
            ChatMessage(role=MessageRole.USER, content=reply),
        ]

from llama_index.core.base.llms.types import ChatMessage, MessageRole
from swiss_ai_hub.core.events.agent import HumanInTheLoopChoiceOption, HumanInTheLoopChoiceQuestion
from swiss_ai_hub.core.i18n import LocaleHandler
from swiss_ai_hub.core.topic_managers import AgentTopicManager
from swiss_ai_hub.core.topics import PartialAgentTopic

from swiss_ai_hub.agent.agents.knowledge_extraction_agent.extraction_request_answer import ExtractionRequestAnswer
from swiss_ai_hub.agent.agents.knowledge_extraction_agent.extraction_request_form_request_event import (
    ExtractionRequestFormRequestEvent,
)
from swiss_ai_hub.agent.agents.knowledge_extraction_agent.extraction_request_form_response_event import (
    ExtractionRequestFormResponseEvent,
)
from swiss_ai_hub.agent.agents.knowledge_extraction_agent.extraction_request_parts import ExtractionRequestParts
from swiss_ai_hub.agent.context.run.run_context import RunContext

READING_KEY = "knowledge_extraction:request_form:reading"
_FORM = "agent.knowledge_extraction_agent.form"
# OpenWebUI's dialog cuts longer texts; cutting here keeps the end visible as an ellipsis.
QUESTION_LENGTH = 500
DESCRIPTION_LENGTH = 240


class ExtractionRequestForm:
    """Asks the user to confirm where, which rows and which columns before any document is read.

    A misread part otherwise only shows in the finished table. Each part is a choice question whose first option keeps
    it as understood and whose second, when there is one, drops it (every document, every row); a free answer corrects
    it. The same parts are the request's text, for clients without a dialog. The reading waits in the run for the
    answer, since the answer resumes the same run.
    """

    request = ExtractionRequestFormRequestEvent
    response = ExtractionRequestFormResponseEvent

    @classmethod
    async def ask(
        cls, reading: ExtractionRequestAnswer, run_context: RunContext, t: LocaleHandler
    ) -> ExtractionRequestFormRequestEvent:
        await run_context.set(READING_KEY, reading.model_dump(mode="json"))
        parts = ExtractionRequestParts.of(reading, t)
        return cls.request(
            question=ExtractionRequestForm.text(parts, t),
            questions=[
                ExtractionRequestForm._question("where", parts.where, bool(reading.locations), True, t),
                ExtractionRequestForm._question("rows", parts.rows, bool(reading.instructions), True, t),
                ExtractionRequestForm._question("columns", parts.columns, bool(reading.fields), False, t),
            ],
            topic=PartialAgentTopic(
                event_type=AgentTopicManager.CONTROL_EVENT, event_name=cls.response.event_name_from_class()
            ),
        )

    @staticmethod
    async def understood(run_context: RunContext) -> ExtractionRequestAnswer:
        return ExtractionRequestAnswer.model_validate(await run_context.get(READING_KEY))

    @staticmethod
    def answered(history: list[ChatMessage], question: str, reply: str) -> list[ChatMessage]:
        """The conversation with the form and the user's reply to it, for reading or searching once more."""
        return [
            *history,
            ChatMessage(role=MessageRole.ASSISTANT, content=question),
            ChatMessage(role=MessageRole.USER, content=reply),
        ]

    @staticmethod
    def text(parts: ExtractionRequestParts, t: LocaleHandler) -> str:
        lines = [f"- {line}" for line in parts.lines(t)]
        return "\n".join([t(f"{_FORM}.intro"), "", *lines, "", t(f"{_FORM}.reply_hint")])

    @staticmethod
    def _question(key: str, value: str, named: bool, droppable: bool, t: LocaleHandler) -> HumanInTheLoopChoiceQuestion:
        """The part as understood first; a part the user named can also be dropped, where dropping means anything."""
        understood = HumanInTheLoopChoiceOption(
            label=t(f"{_FORM}.as_understood"), description=ExtractionRequestForm._clip(value, DESCRIPTION_LENGTH)
        )
        anything = HumanInTheLoopChoiceOption(
            label=t(f"{_FORM}.{key}.anything"), description=t(f"{_FORM}.{key}.anything_description")
        )
        options = [understood, anything] if named and droppable else [understood if named else anything]
        return HumanInTheLoopChoiceQuestion(
            id=key,
            header=t(f"{_FORM}.{key}.header"),
            question=ExtractionRequestForm._clip(t(f"{_FORM}.{key}.question", value=value), QUESTION_LENGTH),
            options=options,
            allow_other=True,
        )

    @staticmethod
    def _clip(text: str, length: int) -> str:
        return text if len(text) <= length else f"{text[: length - 1]}…"

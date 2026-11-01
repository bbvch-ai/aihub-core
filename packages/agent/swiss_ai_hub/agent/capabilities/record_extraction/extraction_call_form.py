from typing import Annotated, Any, ClassVar, Self

from pydantic import BaseModel, Field
from swiss_ai_hub.core.generative_ai import BucketNamespacePair, KnowledgeDocumentCriteria, KnowledgeDocumentListing
from swiss_ai_hub.core.i18n import LocaleHandler
from swiss_ai_hub.core.topic_managers import AgentTopicManager
from swiss_ai_hub.core.topics import PartialAgentTopic

from swiss_ai_hub.agent.capabilities.record_extraction.extract_records_tool_arguments import (
    ExtractRecordsToolArguments,
)
from swiss_ai_hub.agent.capabilities.record_extraction.extraction_call_form_request_event import (
    ExtractionCallFormRequestEvent,
)
from swiss_ai_hub.agent.capabilities.record_extraction.extraction_call_form_response_event import (
    ExtractionCallFormResponseEvent,
)
from swiss_ai_hub.agent.capabilities.record_extraction.extraction_form import FORM, ExtractionForm
from swiss_ai_hub.agent.capabilities.record_extraction.extraction_form_part import ExtractionFormPart
from swiss_ai_hub.agent.capabilities.record_extraction.extraction_planner import ExtractionPlanner
from swiss_ai_hub.agent.capabilities.record_extraction.written_location import WrittenLocation
from swiss_ai_hub.agent.context.run.run_context import RunContext

_PENDING_KEY = "record_extraction:call_form:{request_id}"
# A correction only the model can apply goes back to it; its next extraction in this run is the corrected one, asked
# no more.
REWRITTEN_KEY = "record_extraction:call_form:rewritten"


class ExtractionCallForm(BaseModel):
    """The request form of a model's extraction call: where (the call's criteria), which rows and which columns, asked
    back before any document is read, and the call as the user answered it.

    The form replaces the yes/no approval of `extract_records`. It asks three parts, not the keywords: the model
    searched for the documents before it called, so keywords could no longer guide that search. A chosen option keeps or
    drops a part; a free answer replaces it as written, a location by the folders, files or years in scope it names.
    A location naming none of them, or a typed reply other than yes or no, goes back to the model, whose next call then
    runs unasked: only the model can tell what such words mean for the call.
    """

    tool_call_id: Annotated[str, Field(description="The call the form asks about.")]
    arguments: Annotated[
        ExtractRecordsToolArguments, Field(description="The call's arguments as the model passed them.")
    ]
    collections: Annotated[
        list[BucketNamespacePair], Field(description="The run's collections the call extracts from.")
    ]
    restricting_glob: Annotated[
        str | None, Field(description="The profile's glob, which the paths a written location names lie within.")
    ] = None

    request: ClassVar[type[ExtractionCallFormRequestEvent]] = ExtractionCallFormRequestEvent
    response: ClassVar[type[ExtractionCallFormResponseEvent]] = ExtractionCallFormResponseEvent

    async def ask(self, folders: str, run_context: RunContext, t: LocaleHandler) -> ExtractionCallFormRequestEvent:
        """`folders`: the largest folders in scope, so the user can name one as the location."""
        parts = self.parts(folders, t)
        event = ExtractionCallFormRequestEvent(
            question=ExtractionForm.text(parts, [], t),
            questions=ExtractionForm.questions(parts, [], t),
            topic=PartialAgentTopic(
                event_type=AgentTopicManager.CONTROL_EVENT,
                event_name=ExtractionCallFormResponseEvent.event_name_from_class(),
            ),
        )
        await run_context.set(_PENDING_KEY.format(request_id=event.event_id), self.model_dump(mode="json"))
        return event

    @classmethod
    async def pending(cls, response: ExtractionCallFormResponseEvent, run_context: RunContext) -> Self:
        return cls.model_validate(
            await run_context.get(_PENDING_KEY.format(request_id=response.request_event.event_id))
        )

    def parts(self, folders: str, t: LocaleHandler) -> list[ExtractionFormPart]:
        arguments = self.arguments
        named_place = any(ExtractionPlanner.describe(criteria) != "every document" for criteria in arguments.any_of)
        where_hint = t(f"{FORM}.where.hint")
        if folders:
            where_hint = f"{where_hint} {t(f'{FORM}.where.folders', folders=folders)}"
        return [
            ExtractionFormPart(
                key="where",
                value=ExtractionPlanner.describe_any_of(arguments.any_of)
                if named_place
                else t(f"{FORM}.where.everything"),
                named=named_place,
                droppable=True,
                hint=where_hint,
            ),
            ExtractionFormPart(
                key="rows",
                value=arguments.instructions or t(f"{FORM}.rows.everything"),
                named=bool(arguments.instructions),
                droppable=True,
                hint=t(f"{FORM}.rows.hint"),
            ),
            ExtractionFormPart(
                key="columns", value=arguments.fields, named=True, droppable=False, hint=t(f"{FORM}.columns.hint")
            ),
        ]

    def answered(
        self, response: str, listing: KnowledgeDocumentListing, t: LocaleHandler
    ) -> ExtractRecordsToolArguments | str:
        """The call's arguments as the user answered the form, or what to tell the model instead. `listing`: the
        documents in scope, which a written location is matched against."""
        answers = ExtractionForm.dialog_answers(response)
        if answers is None:
            if ExtractionForm.is_yes(response):
                return self.arguments
            if ExtractionForm.is_no(response):
                return t(f"{FORM}.declined")
            return t(f"{FORM}.rewritten", reply=response.strip())
        update: dict = {}
        where, rows, columns = answers.get("where"), answers.get("rows"), answers.get("columns")
        if (place := ExtractionForm.written(where)) is not None:
            criteria = WrittenLocation.criteria(place, listing)
            if criteria is None:
                return t(f"{FORM}.rewritten", reply=self._as_answered(answers, t))
            update["any_of"] = criteria
        elif ExtractionForm.dropped(where):
            update["any_of"] = [KnowledgeDocumentCriteria()]
        if (condition := ExtractionForm.written(rows)) is not None:
            update["instructions"] = condition
        elif ExtractionForm.dropped(rows):
            update["instructions"] = None
        if (values := ExtractionForm.written(columns)) is not None:
            update["fields"] = values
        return self.arguments.model_copy(update=update)

    def _as_answered(self, answers: dict[str, dict[str, Any]], t: LocaleHandler) -> str:
        """Every part as the user answered it, for the model to apply."""
        lines = []
        for part in self.parts("", t):
            answer = answers.get(part.key)
            value = ExtractionForm.written(answer)
            if value is None:
                value = t(f"{FORM}.{part.key}.anything") if ExtractionForm.dropped(answer) else part.value
            lines.append(ExtractionForm.line(part.key, value, t))
        return " · ".join(lines)

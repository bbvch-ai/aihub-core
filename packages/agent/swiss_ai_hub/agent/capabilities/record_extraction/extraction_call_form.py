import re
from typing import Annotated, ClassVar, Self

from pydantic import BaseModel, Field
from swiss_ai_hub.core.generative_ai import BucketNamespacePair, KnowledgeDocumentCriteria
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
from swiss_ai_hub.agent.context.run.run_context import RunContext

_PENDING_KEY = "record_extraction:call_form:{request_id}"
# A typed correction goes back to the model; its next extraction in this run is the corrected one, asked no more.
REWRITTEN_KEY = "record_extraction:call_form:rewritten"
# A word with a folder separator, a glob character or a file extension names a place; anything else is text.
_PLACE = re.compile(r"[/*?\[]|\.[A-Za-z0-9]{1,5}$")


class ExtractionCallForm(BaseModel):
    """The request form of a model's extraction call: where (the call's criteria), which rows and which columns, asked
    back before any document is read, and the call as the user answered it.

    The form replaces the yes/no approval of `extract_records`. It asks three parts, not the keywords: the model
    searched for the documents before it called, so keywords could no longer guide that search. A chosen option keeps or
    drops a part; a free answer replaces it as written, a place by its path and anything else as a text the documents
    contain. A typed reply other than yes or no goes back to the model, whose next call then runs unasked.
    """

    tool_call_id: Annotated[str, Field(description="The call the form asks about.")]
    arguments: Annotated[
        ExtractRecordsToolArguments, Field(description="The call's arguments as the model passed them.")
    ]
    collections: Annotated[
        list[BucketNamespacePair], Field(description="The run's collections the call extracts from.")
    ]

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

    def answered(self, response: str, t: LocaleHandler) -> ExtractRecordsToolArguments | str:
        """The call's arguments as the user answered the form, or what to tell the model instead."""
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
            update["any_of"] = [ExtractionCallForm._criteria(place)]
        elif ExtractionForm.dropped(where):
            update["any_of"] = [KnowledgeDocumentCriteria()]
        if (condition := ExtractionForm.written(rows)) is not None:
            update["instructions"] = condition
        elif ExtractionForm.dropped(rows):
            update["instructions"] = None
        if (values := ExtractionForm.written(columns)) is not None:
            update["fields"] = values
        return self.arguments.model_copy(update=update)

    @staticmethod
    def rewrites(response: str) -> bool:
        """Whether the answer is a typed correction the model applies, rather than the dialog's or a yes or a no."""
        typed = ExtractionForm.dialog_answers(response) is None
        return typed and not ExtractionForm.is_yes(response) and not ExtractionForm.is_no(response)

    @staticmethod
    def _criteria(place: str) -> KnowledgeDocumentCriteria:
        """A written place: a path or folder as a glob, anything else as text the documents contain."""
        if not _PLACE.search(place):
            return KnowledgeDocumentCriteria(content_query=place)
        path = place.strip().strip("/")
        if any(character in path for character in "*?[") or re.search(r"\.[A-Za-z0-9]{1,5}$", path):
            return KnowledgeDocumentCriteria(path_glob=path if path.startswith("**") else f"**/{path}")
        return KnowledgeDocumentCriteria(path_glob=f"{path}/**")

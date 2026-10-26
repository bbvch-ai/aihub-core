from llama_index.core.base.llms.types import ChatMessage
from swiss_ai_hub.core.auth import UserIdentity
from swiss_ai_hub.core.displayers import EventDisplayer
from swiss_ai_hub.core.events.agent import ExtractRecordsEvent
from swiss_ai_hub.core.generative_ai import InvalidPathPatternError, KnowledgeDocumentListing, KnowledgeDocumentReader
from swiss_ai_hub.core.i18n import LocaleHandler

from swiss_ai_hub.agent.agents.knowledge_extraction_agent.extraction_notices import ExtractionNotices
from swiss_ai_hub.agent.agents.knowledge_extraction_agent.extraction_request_answer import ExtractionRequestAnswer
from swiss_ai_hub.agent.agents.knowledge_extraction_agent.extraction_request_reading import ExtractionRequestReading
from swiss_ai_hub.agent.agents.knowledge_extraction_agent.knowledge_extraction_agent_config import (
    KnowledgeExtractionAgentConfig,
)
from swiss_ai_hub.agent.agents.knowledge_extraction_agent.requested_location import RequestedLocation
from swiss_ai_hub.agent.capabilities.knowledge_documents.knowledge_document_run_scope import (
    KnowledgeDocumentRunScope,
)
from swiss_ai_hub.agent.capabilities.record_extraction.record_extraction import RecordExtraction
from swiss_ai_hub.agent.capabilities.record_extraction.sample_awaiting_confirmation import SampleAwaitingConfirmation
from swiss_ai_hub.agent.capabilities.record_extraction.selection_facets import SelectionFacets

_MESSAGES = "agent.knowledge_extraction_agent.messages"


class WholeScopeRequest:
    """A request answered from every document in the profile's scope, or the confirmation of a sample.

    Without discovery the request is read once, and only the places the user named narrow the scope, so no document
    is left out for its wording. With discovery the model searches instead; this still runs while a sample awaits the
    user's decision, because only a reading of the message tells a "yes" from a new request.
    """

    @staticmethod
    async def extraction(
        history: list[ChatMessage],
        scope: KnowledgeDocumentRunScope,
        agent_config: KnowledgeExtractionAgentConfig,
        awaiting: SampleAwaitingConfirmation | None,
        displayer: EventDisplayer,
        user: UserIdentity | None,
        t: LocaleHandler,
        locale: str,
    ) -> ExtractRecordsEvent | str | None:
        """The extraction to run, the notice to answer with instead, or None to let the model search (discovery)."""
        listing = await WholeScopeRequest._listing(scope)
        facets = SelectionFacets.lines(listing.documents, t)
        instructions = agent_config.instructions.in_locale(locale) if agent_config.instructions else None
        reading = await ExtractionRequestReading.ask(
            history, scope, facets, instructions, awaiting is not None, agent_config.llm, displayer, user, t
        )
        notices = ExtractionNotices.for_table(scope, False, t)
        if awaiting is not None and reading is not None and reading.confirms_sample:
            return RecordExtraction.confirm_sample(scope.pairs(), notices)
        if agent_config.discovery:
            return None
        if reading is None:
            return t(f"{_MESSAGES}.no_request")
        if not reading.is_table_request:
            return t(f"{_MESSAGES}.not_a_table_request")
        if not reading.locations:
            written = RequestedLocation.written_in(ExtractionRequestReading.last_request(history))
            reading = reading.model_copy(update={"locations": written})
        if reading.locations and not WholeScopeRequest._anything_at(listing, reading):
            places = ", ".join(f"`{location.describe()}`" for location in reading.locations)
            return "\n\n".join([t(f"{_MESSAGES}.nothing_at_location", locations=places), *facets])
        return RecordExtraction.extract(
            reading.selection,
            reading.fields,
            scope.pairs(),
            reading.instructions,
            reading.row_terms,
            notices=notices,
            document_terms=reading.document_terms,
        )

    @staticmethod
    async def _listing(scope: KnowledgeDocumentRunScope) -> KnowledgeDocumentListing:
        listing = await KnowledgeDocumentReader.list_documents(scope.pairs())
        return listing.matching_glob(scope.restricting_glob) if scope.restricting_glob else listing

    @staticmethod
    def _anything_at(listing: KnowledgeDocumentListing, reading: ExtractionRequestAnswer) -> bool:
        """Whether a named place holds a document in scope; an invalid pattern is left to the extraction to report."""
        for location in reading.locations:
            try:
                matched = listing.matching_glob(location.path_glob) if location.path_glob else listing
                matched = matched.matching_regex(location.path_regex) if location.path_regex else matched
            except InvalidPathPatternError:
                return True
            if matched.documents:
                return True
        return False

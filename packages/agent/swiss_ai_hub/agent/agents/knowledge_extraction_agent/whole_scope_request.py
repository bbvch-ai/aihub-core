from llama_index.core.base.llms.types import ChatMessage
from swiss_ai_hub.core.auth import UserIdentity
from swiss_ai_hub.core.displayers import EventDisplayer
from swiss_ai_hub.core.events.agent import ExtractRecordsEvent
from swiss_ai_hub.core.generative_ai import (
    InvalidPathPatternError,
    KnowledgeDocumentCriteria,
    KnowledgeDocumentListing,
    KnowledgeDocumentReader,
    KnowledgeDocumentSelection,
    KnowledgeDocumentSummary,
)
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
_PLACE_FIELDS = ("collection", "path_glob", "path_regex")


class WholeScopeRequest:
    """A request read over every document in the profile's scope, or the confirmation of a sample.

    The request is read once, in either mode, for the user to confirm in the request form; only a reading tells a "yes"
    to a waiting sample from a new request. The files the message names replace the places a model made of them before
    the form shows them, so what the user confirms is what is read. Without discovery, only the places the user
    confirmed narrow the scope, so no document is left out for its wording.
    """

    @staticmethod
    async def listing(scope: KnowledgeDocumentRunScope) -> KnowledgeDocumentListing:
        """The documents in scope, listed once per step and handed to every method that reads them."""
        listing = await KnowledgeDocumentReader.list_documents(scope.pairs())
        return listing.matching_glob(scope.restricting_glob) if scope.restricting_glob else listing

    @staticmethod
    async def reading(
        history: list[ChatMessage],
        scope: KnowledgeDocumentRunScope,
        listing: KnowledgeDocumentListing,
        agent_config: KnowledgeExtractionAgentConfig,
        awaiting: SampleAwaitingConfirmation | None,
        displayer: EventDisplayer,
        user: UserIdentity | None,
        t: LocaleHandler,
        locale: str,
    ) -> ExtractRecordsEvent | ExtractionRequestAnswer | str:
        """The confirmation of the waiting sample, the request as read for the user to confirm, or the notice to
        answer with instead."""
        reading = await WholeScopeRequest.read(
            history, scope, listing, agent_config, awaiting is not None, displayer, user, t, locale
        )
        if awaiting is not None and reading is not None and reading.confirms_sample:
            return RecordExtraction.confirm_sample(scope.pairs(), ExtractionNotices.for_table(scope, False, t))
        if reading is None:
            return t(f"{_MESSAGES}.no_request")
        if not reading.is_table_request:
            return t(f"{_MESSAGES}.not_a_table_request")
        return reading

    @staticmethod
    async def read(
        history: list[ChatMessage],
        scope: KnowledgeDocumentRunScope,
        listing: KnowledgeDocumentListing,
        agent_config: KnowledgeExtractionAgentConfig,
        awaiting_sample: bool,
        displayer: EventDisplayer,
        user: UserIdentity | None,
        t: LocaleHandler,
        locale: str,
    ) -> ExtractionRequestAnswer | None:
        """The conversation's last message read as a table request, with the collections, folders and years in scope
        to name, and the files that message names in place of the places the model made of them."""
        facets = SelectionFacets.lines(listing.documents, t)
        instructions = agent_config.instructions.in_locale(locale) if agent_config.instructions else None
        reading = await ExtractionRequestReading.ask(
            history, scope, facets, instructions, awaiting_sample, agent_config.llm, displayer, user, t
        )
        if reading is None:
            return None
        named = WholeScopeRequest._named_files(ExtractionRequestReading.last_request(history), listing)
        if not named:
            return reading
        return reading.model_copy(update={"locations": WholeScopeRequest._narrowed(reading, named, listing)})

    @staticmethod
    def unmatched(reading: ExtractionRequestAnswer, listing: KnowledgeDocumentListing, t: LocaleHandler) -> list[str]:
        """The notice naming each understood place that holds no document, shown in the form before the user confirms
        it; an invalid pattern is left to the extraction to report."""
        empty = [location for location in reading.locations if WholeScopeRequest._at(listing, location) == []]
        if not empty:
            return []
        places = ", ".join(f"`{location.describe()}`" for location in empty)
        return [t(f"{_MESSAGES}.nothing_at_understood_location", locations=places)]

    @staticmethod
    def extraction_of(
        reading: ExtractionRequestAnswer,
        scope: KnowledgeDocumentRunScope,
        listing: KnowledgeDocumentListing,
        t: LocaleHandler,
    ) -> ExtractRecordsEvent | str:
        """The extraction of a confirmed reading over the whole scope, or the notice that its places hold nothing. The
        places are taken as confirmed: the user may have widened or changed what the message named."""
        if reading.locations and not WholeScopeRequest._anything_at(listing, reading.locations):
            places = ", ".join(f"`{location.describe()}`" for location in reading.locations)
            facets = SelectionFacets.lines(listing.documents, t)
            return "\n\n".join([t(f"{_MESSAGES}.nothing_at_location", locations=places), *facets])
        return RecordExtraction.extract(
            reading.selection,
            reading.fields,
            scope.pairs(),
            reading.instructions,
            reading.row_terms,
            notices=[
                *ExtractionNotices.for_calculation(reading.calculation, t),
                *ExtractionNotices.for_table(scope, False, t),
            ],
            document_terms=reading.document_terms,
        )

    @staticmethod
    async def within(
        selection: KnowledgeDocumentSelection,
        locations: list[RequestedLocation],
        scope: KnowledgeDocumentRunScope,
        t: LocaleHandler,
    ) -> KnowledgeDocumentSelection | str:
        """The model's selection at the places the user confirmed, or the notice that those places hold nothing. The
        confirmed Location replaces any collection or path the model set: a model combining it with a file the message
        named selected nothing and reported the confirmed folder as empty."""
        places = [location for location in locations if location.is_place]
        if not places:
            return selection
        listing = await WholeScopeRequest.listing(scope)
        if not WholeScopeRequest._anything_at(listing, places):
            described = ", ".join(f"`{location.describe()}`" for location in places)
            facets = SelectionFacets.lines(listing.documents, t)
            return "\n\n".join([t(f"{_MESSAGES}.nothing_at_location", locations=described), *facets])
        entries = [WholeScopeRequest._at_place(entry, place, listing) for entry in selection.any_of for place in places]
        unique = {entry.model_dump_json(): entry for entry in entries}
        return KnowledgeDocumentSelection(any_of=list(unique.values()))

    @staticmethod
    def _at_place(
        entry: KnowledgeDocumentCriteria, place: RequestedLocation, listing: KnowledgeDocumentListing
    ) -> KnowledgeDocumentCriteria:
        """The entry with the place's collection and path instead of its own. Documents the model chose by id stay
        chosen when they lie at the place; when none do, the whole place is read and the condition decides the rows."""
        ids = sorted(set(entry.document_ids) & WholeScopeRequest._ids_at(listing, place))
        place_fields = {field: getattr(place, field) for field in _PLACE_FIELDS}
        return entry.model_copy(update=place_fields | {"document_ids": ids})

    @staticmethod
    def _named_files(message: str, listing: KnowledgeDocumentListing) -> list[RequestedLocation]:
        """The files the message names, as written paths or by their names in scope."""
        named = RequestedLocation.written_in(message)
        named += RequestedLocation.named_in(message, [document.path for document in listing.documents])
        return list({location.path_glob: location for location in named}.values())

    @staticmethod
    def _narrowed(
        reading: ExtractionRequestAnswer, named: list[RequestedLocation], listing: KnowledgeDocumentListing
    ) -> list[RequestedLocation]:
        """The named files win over the places the reading made of them: a model reads `a/b/x.pdf` as `a/b/**` and
        extracts the whole folder. A place that holds none of the named files is another place the user asked for."""
        files = set().union(*(WholeScopeRequest._ids_at(listing, location) for location in named))
        others = [
            location
            for location in reading.locations
            if location not in named and not files & WholeScopeRequest._ids_at(listing, location)
        ]
        return [*named, *others]

    @staticmethod
    def _anything_at(listing: KnowledgeDocumentListing, locations: list[RequestedLocation]) -> bool:
        """Whether a place holds a document in scope; an invalid pattern is left to the extraction to report."""
        return any(WholeScopeRequest._at(listing, location) != [] for location in locations)

    @staticmethod
    def _at(listing: KnowledgeDocumentListing, location: RequestedLocation) -> list[KnowledgeDocumentSummary] | None:
        """The documents in scope at a place; None for an invalid pattern. A collection outside the scope holds none."""
        matched = listing.in_collection(location.collection) if location.collection else listing
        try:
            matched = matched.matching_glob(location.path_glob) if location.path_glob else matched
            matched = matched.matching_regex(location.path_regex) if location.path_regex else matched
        except InvalidPathPatternError:
            return None
        return matched.documents

    @staticmethod
    def _ids_at(listing: KnowledgeDocumentListing, location: RequestedLocation) -> set[str]:
        return {document.id for document in WholeScopeRequest._at(listing, location) or []}

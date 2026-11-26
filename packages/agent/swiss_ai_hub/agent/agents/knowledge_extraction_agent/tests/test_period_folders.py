"""A first reading's location loses the date folders that only repeat the period the request names (e2e N1 of #2349):
"invoice totals 2025" read as invoices/2025/** plus the period left out every undated invoice. Only literal date
folders of a path_glob that lie within the period are replaced, by `**`, so a location only ever matches more; a
folder dated outside or across the period, a regex, a folder that names more than a date and a path the message writes
stay as the model read them."""

import logging
from datetime import UTC, date, datetime

import pytest
from swiss_ai_hub.core.generative_ai import (
    BucketNamespacePair,
    KnowledgeDocumentListing,
    KnowledgeDocumentSummary,
    PathDateRange,
)

from swiss_ai_hub.agent.agents.knowledge_extraction_agent.extraction_request_answer import ExtractionRequestAnswer
from swiss_ai_hub.agent.agents.knowledge_extraction_agent.requested_location import RequestedLocation

YEAR_2025 = PathDateRange(start=date(2025, 1, 1), end=date(2025, 12, 31))
Q1_2025 = PathDateRange(start=date(2025, 1, 1), end=date(2025, 3, 31))
SINCE_2024 = PathDateRange(start=date(2024, 1, 1))
MESSAGE = "invoice totals 2025"
PATHS = (
    "invoices/acme-undated.pdf",
    "invoices/2024/a.pdf",
    "invoices/2025/b.pdf",
    "invoices/2025/q1/c.pdf",
    "invoices/2025/q2/d.pdf",
    "invoices/2025/acme/e.pdf",
    "invoices/2024/acme/f.pdf",
    "invoices/acme/g.pdf",
    "invoices/2025/03/h.pdf",
    "2025/i.pdf",
    "statements/2025/j.pdf",
    "archive/invoices/2025/k.pdf",
)


def _glob(glob: str, period: PathDateRange = YEAR_2025, message: str = MESSAGE) -> str | None:
    location = RequestedLocation(collection=None, path_glob=glob, path_regex=None)
    return location.without_period_folders(period, message).path_glob


def _reading(
    *globs: str, period: tuple[str | None, str | None] = ("2025-01-01", "2025-12-31")
) -> ExtractionRequestAnswer:
    return ExtractionRequestAnswer(
        is_table_request=True,
        confirms_sample=False,
        locations=[RequestedLocation(collection=None, path_glob=glob, path_regex=None) for glob in globs],
        fields="invoice number, total",
        period_start=period[0],
        period_end=period[1],
        instructions=None,
        calculation=None,
        document_kind=None,
        row_terms=None,
        document_terms=None,
    )


def _matched(glob: str) -> set[str]:
    documents = [
        KnowledgeDocumentSummary(
            id=path,
            collection=BucketNamespacePair(bucket_name="finance", namespace_name="invoices"),
            collection_name="finance/invoices",
            path=path,
            filename=path.rsplit("/", 1)[-1],
            title=path,
            file_type="pdf",
            updated_at=datetime(2025, 1, 1, tzinfo=UTC),
        )
        for path in PATHS
    ]
    return {
        document.path for document in KnowledgeDocumentListing.from_summaries(documents).matching_glob(glob).documents
    }


@pytest.mark.parametrize(
    ("glob", "period", "widened"),
    [
        ("invoices/2025/**", YEAR_2025, "invoices/**"),
        ("invoices/2025", YEAR_2025, "invoices/**"),
        ("invoices/2025/q1", Q1_2025, "invoices/**"),
        ("invoices/2025/q1/**", Q1_2025, "invoices/**"),
        ("invoices/2025/q1/**", YEAR_2025, "invoices/**"),
        ("invoices/2025/03/**", YEAR_2025, "invoices/**"),
        ("invoices/2025/acme/**", YEAR_2025, "invoices/**/acme/**"),
        ("invoices/2025/*.pdf", YEAR_2025, "invoices/**/*.pdf"),
        ("2025/**", YEAR_2025, "**"),
        ("**/2025/**", YEAR_2025, "**"),
        ("invoices/2025/**", SINCE_2024, "invoices/**"),
    ],
)
def test_a_date_folder_within_the_period_becomes_any_folders(glob: str, period: PathDateRange, widened: str):
    assert _glob(glob, period) == widened


@pytest.mark.parametrize(
    ("glob", "period"),
    [
        ("invoices/2024/**", YEAR_2025),
        ("invoices/2025/**", Q1_2025),
        ("invoices/2025/q2/**", Q1_2025),
        ("invoices/2024/2025/**", YEAR_2025),
        ("invoices-2025/**", YEAR_2025),
        ("invoices/Rechnungen 2025/**", YEAR_2025),
        ("invoices/2025*/**", YEAR_2025),
        ("invoices/{2024,2025}/**", YEAR_2025),
        ("invoices/**", YEAR_2025),
        ("invoices/acme/**", YEAR_2025),
    ],
)
def test_a_folder_outside_or_across_the_period_or_more_than_a_date_stays(glob: str, period: PathDateRange):
    """A 2025 folder with Q1 2025 is wider than the period: the model or the user chose more than the period names,
    and the path filter keeps its Q1 documents and its undated ones anyway."""
    assert _glob(glob, period) == glob


@pytest.mark.parametrize(
    ("glob", "message"),
    [
        ("invoices/2025/**", "invoice totals 2025 from invoices/2025"),
        ("invoices/2025/q1/**", "totals of Q1 2025 in 2025/Q1"),
        ("**/invoices/2025/a.pdf", "the total of invoices/2025/a.pdf"),
    ],
)
def test_a_date_folder_the_message_writes_as_a_path_stays(glob: str, message: str):
    assert _glob(glob, Q1_2025 if "q1" in glob else YEAR_2025, message) == glob


def test_a_regex_is_never_read():
    location = RequestedLocation(collection=None, path_glob=None, path_regex="invoices/2025/")
    both = RequestedLocation(collection=None, path_glob="invoices/2025/**", path_regex="acme")

    assert location.without_period_folders(YEAR_2025, MESSAGE) == location
    assert both.without_period_folders(YEAR_2025, MESSAGE) == both


@pytest.mark.parametrize(
    ("glob", "period"),
    [
        ("invoices/2025/**", YEAR_2025),
        ("invoices/2025/q1", Q1_2025),
        ("invoices/2025/q1/**", YEAR_2025),
        ("invoices/2025/acme/**", YEAR_2025),
        ("invoices/2025/03/**", YEAR_2025),
        ("2025/**", YEAR_2025),
        ("**/2025/**", YEAR_2025),
        ("invoices/2025/*.pdf", YEAR_2025),
    ],
)
def test_a_widened_glob_matches_every_path_the_model_s_glob_matched_and_the_undated_ones(
    glob: str, period: PathDateRange
):
    widened = _glob(glob, period)

    assert widened is not None
    assert _matched(glob) <= _matched(widened)
    assert _matched(widened) - _matched(glob)


def test_without_a_period_the_reading_keeps_its_locations():
    reading = _reading("invoices/2025/**", period=(None, None))

    assert reading.without_period_folders(MESSAGE) == reading


def test_the_reading_widens_its_locations_and_drops_doubles():
    reading = _reading("invoices/2025/**", "invoices/2025/q1/**", "invoices/**", "statements/**")

    assert [location.path_glob for location in reading.without_period_folders(MESSAGE).locations] == [
        "invoices/**",
        "statements/**",
    ]


def test_a_location_widened_to_every_document_makes_the_whole_scope_the_place():
    """Keeping statements/** alone would read fewer documents than 2025/** and statements/** together did."""
    reading = _reading("2025/**", "statements/**")

    widened = reading.without_period_folders(MESSAGE)

    assert widened.locations == []
    assert widened.selection.any_of[0].path_glob is None
    assert widened.selection.path_date_range == YEAR_2025


def test_a_collection_keeps_its_widened_places_apart_and_never_widens_to_the_whole_scope():
    """A path starts inside its collection: `2025/**` of one collection widened to `**` is that whole collection, and
    the same widened glob in two collections stays two places."""
    reading = _reading("2025/**").model_copy(
        update={
            "locations": [
                RequestedLocation(collection="kb/finance", path_glob="2025/**", path_regex=None),
                RequestedLocation(collection="kb/legal", path_glob="2025/**", path_regex=None),
            ]
        }
    )

    widened = reading.without_period_folders(MESSAGE)

    assert [(location.collection, location.path_glob) for location in widened.locations] == [
        ("kb/finance", "**"),
        ("kb/legal", "**"),
    ]


def test_a_reading_with_nothing_to_widen_is_returned_as_it_is():
    reading = _reading("invoices/2024/**", "statements/**")

    assert reading.without_period_folders(MESSAGE) is reading


def test_widening_is_logged_with_the_locations_before_and_after(caplog: pytest.LogCaptureFixture):
    with caplog.at_level(logging.INFO):
        _reading("invoices/2025/**").without_period_folders(MESSAGE)

    assert "['invoices/2025/**'] widened to ['invoices/**']" in caplog.text


def test_a_folder_written_with_backslashes_counts_as_written():
    """Review suggestion 2: OneDrive and SMB users write Windows paths."""
    assert _glob("invoices/2025/**", message="invoice totals 2025 from invoices\\2025") == "invoices/2025/**"


def test_a_leading_slash_that_widens_to_every_document_makes_the_whole_scope_the_place():
    """Review suggestion 4: `/**` matches every path, since a glob loses its leading slash before matching."""
    reading = _reading("/2025/**", "statements/**")

    assert reading.without_period_folders(MESSAGE).locations == []


@pytest.mark.parametrize("glob", ["invoices/2025*/q1/**", "invoices/{2024,2025}/q1/**", "invoices/2025?/03/**"])
def test_a_pattern_segment_dates_no_folder_below_it(glob: str):
    """Review suggestion 5: a quarter under `2025*` took its year from the pattern and was stripped."""
    assert _glob(glob, Q1_2025) == glob

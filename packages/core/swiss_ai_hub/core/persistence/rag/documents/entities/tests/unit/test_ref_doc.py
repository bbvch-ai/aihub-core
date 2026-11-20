from contextlib import contextmanager
from unittest.mock import MagicMock, patch

import pytest
from mongoengine import NotUniqueError

from swiss_ai_hub.core.persistence.rag.documents.entities.ref_doc import RefDoc
from swiss_ai_hub.core.persistence.rag.documents.utils.id_utils import source_to_doc_id

pytestmark = pytest.mark.unit

_MODULE = "swiss_ai_hub.core.persistence.rag.documents.entities.ref_doc"
_SWITCH_DB = f"{_MODULE}.switch_db"


@contextmanager
def _switched(queryset: MagicMock):
    switched = MagicMock()
    switched.objects.return_value = queryset
    yield switched


def _switched_to(switched: MagicMock):
    @contextmanager
    def _cm(*_args, **_kwargs):
        yield switched

    return _cm


_CLEARED_FAILURE = {
    "unset__data__metadata__ingestion_failed_attempts": True,
    "unset__data__metadata__ingestion_failed_at": True,
    "unset__data__metadata__ingestion_gave_up": True,
}


class TestMarkIngested:
    def test_sets_the_flag_and_ends_any_reported_failure_but_leaves_updated_at(self) -> None:
        """`updated_at` carries the source file's timestamp — it feeds asset data versions and the
        default document sort, so marking a document ingested must not touch it."""
        queryset = MagicMock()
        queryset.update_one.return_value = 1

        with patch(_SWITCH_DB, return_value=_switched(queryset)):
            assert RefDoc.mark_ingested(db_alias="my_db", doc_id="doc1") is True

        queryset.update_one.assert_called_once_with(set__data__metadata__is_ingested=True, **_CLEARED_FAILURE)

    def test_returns_false_when_no_document_matched(self) -> None:
        queryset = MagicMock()
        queryset.update_one.return_value = 0

        with patch(_SWITCH_DB, return_value=_switched(queryset)):
            assert RefDoc.mark_ingested(db_alias="my_db", doc_id="ghost") is False


class TestGetOrCreatePlaceholder:
    _SOURCE = "s3://my-bucket/reports/q3.pdf"

    def test_resets_an_existing_document_whatever_its_state(self) -> None:
        """The reset matches on id alone, so a re-upload of an *already pending* document still bumps
        `updated_at`. That bump is the only signal the UI has to tell a re-upload apart from a document
        still awaiting deletion — ids are derived from the source URI, so both reuse the same one."""
        queryset = MagicMock()
        queryset.update_one.return_value = 1
        switched = MagicMock()
        switched.objects.return_value = queryset

        with (
            patch(_SWITCH_DB, _switched_to(switched)),
            patch(f"{_MODULE}.time.time", return_value=1_700_000_000.9),
        ):
            ref_doc, created = RefDoc.get_or_create_placeholder(
                db_alias="my_db", source=self._SOURCE, namespace="reports"
            )

        assert created is False
        assert ref_doc is switched.objects.get.return_value
        switched.objects.assert_called_once_with(id=source_to_doc_id(self._SOURCE))
        queryset.update_one.assert_called_once_with(
            set__data__metadata__is_ingested=False,
            set__data__metadata__updated_at=1_700_000_000,
            **_CLEARED_FAILURE,
        )

    def test_creates_a_placeholder_when_the_document_is_unknown(self) -> None:
        queryset = MagicMock()
        queryset.update_one.return_value = 0
        switched = MagicMock()
        switched.objects.return_value = queryset
        placeholder = MagicMock()

        with (
            patch(_SWITCH_DB, _switched_to(switched)),
            patch.object(RefDoc, "create_placeholder", return_value=placeholder) as create_placeholder,
        ):
            ref_doc, created = RefDoc.get_or_create_placeholder(
                db_alias="my_db", source=self._SOURCE, namespace="reports", document_title="Q3"
            )

        assert created is True
        assert ref_doc is placeholder
        create_placeholder.assert_called_once_with("my_db", self._SOURCE, "reports", "Q3")


class TestRecordIngestionFailure:
    def _record(self, switched: MagicMock, *, gave_up: bool = False) -> bool:
        with patch(_SWITCH_DB, _switched_to(switched)):
            return RefDoc.record_ingestion_failure(
                db_alias="my_db",
                doc_id="doc1",
                failed_attempts=2,
                gave_up=gave_up,
                failed_at=1_700_000_000,
                attempt_started_at=1_699_999_000,
            )

    def test_a_pending_document_is_reported_failed(self) -> None:
        switched = MagicMock()
        pending = switched.objects.return_value
        pending.count.return_value = 1

        assert self._record(switched, gave_up=True) is True

        switched.objects.assert_called_once_with(
            id="doc1", data__metadata__is_ingested=False, data__metadata__updated_at__lt=1_699_999_000
        )
        pending.filter.return_value.update_one.assert_called_once_with(
            set__data__metadata__ingestion_failed_attempts=2,
            set__data__metadata__ingestion_gave_up=True,
            set__data__metadata__ingestion_failed_at=1_700_000_000,
        )

    def test_an_ingested_unknown_or_re_uploaded_document_is_left_alone(self) -> None:
        """Once its nodes are in the vector store a document is retrievable, so a later failure of its
        summaries must not show it as failed; and a record dated after the failure was re-uploaded since."""
        switched = MagicMock()
        switched.objects.return_value.count.return_value = 0

        assert self._record(switched) is False

        switched.objects.return_value.filter.assert_not_called()


class TestPlaceholderInsertion:
    """A placeholder never replaces a record: save() of a document with an id would, losing a parse that finished."""

    _SOURCE = "s3://my-bucket/reports/q3.pdf"

    def test_a_placeholder_is_inserted_never_saved_over_a_record(self) -> None:
        switched = MagicMock()

        with patch(_SWITCH_DB, _switched_to(switched)):
            RefDoc.create_placeholder("my_db", self._SOURCE, namespace="reports")

        switched.return_value.save.assert_called_once_with(force_insert=True)

    def test_a_failed_placeholder_carries_the_failure_and_is_dated_to_it(self) -> None:
        switched = MagicMock()

        with patch(_SWITCH_DB, _switched_to(switched)):
            created = RefDoc.create_failed_placeholder(
                "my_db", self._SOURCE, namespace="reports", failed_attempts=4, gave_up=True, failed_at=1_700_000_000
            )

        assert created is True
        metadata = switched.call_args.kwargs["data"].metadata
        assert (metadata.ingestion_failed_attempts, metadata.ingestion_gave_up) == (4, True)
        assert metadata.ingestion_failed_at == metadata.updated_at == 1_700_000_000
        assert metadata.document_title == "q3.pdf"
        assert metadata.is_ingested is False

    def test_a_failed_placeholder_is_not_created_over_an_existing_record(self) -> None:
        switched = MagicMock()
        switched.return_value.save.side_effect = NotUniqueError("duplicate key")

        with patch(_SWITCH_DB, _switched_to(switched)):
            created = RefDoc.create_failed_placeholder(
                "my_db", self._SOURCE, namespace="reports", failed_attempts=1, gave_up=False, failed_at=1_700_000_000
            )

        assert created is False


class TestClearIngestionFailures:
    def test_only_documents_reported_failed_are_cleared(self) -> None:
        switched = MagicMock()
        switched.objects.return_value.update.return_value = 1

        with patch(_SWITCH_DB, _switched_to(switched)):
            assert RefDoc.clear_ingestion_failures("my_db", ["doc1", "doc2"]) == 1

        switched.objects.assert_called_once_with(
            id__in=["doc1", "doc2"], data__metadata__ingestion_failed_attempts__exists=True
        )
        switched.objects.return_value.update.assert_called_once_with(**_CLEARED_FAILURE)


class TestIdLookups:
    def test_all_ids_are_read_as_a_projection(self) -> None:
        switched = MagicMock()
        switched.objects.scalar.return_value = ["doc1", "doc2"]

        with patch(_SWITCH_DB, _switched_to(switched)):
            assert RefDoc.get_all_ids(db_alias="my_db") == {"doc1", "doc2"}

        switched.objects.scalar.assert_called_once_with("id")

    def test_existing_ids_are_the_subset_that_still_has_a_document(self) -> None:
        switched = MagicMock()
        switched.objects.filter.return_value.scalar.return_value = ["doc1"]

        with patch(_SWITCH_DB, _switched_to(switched)):
            assert RefDoc.get_existing_ids(db_alias="my_db", doc_ids=["doc1", "gone"]) == {"doc1"}

        switched.objects.filter.assert_called_once_with(id__in=["doc1", "gone"])

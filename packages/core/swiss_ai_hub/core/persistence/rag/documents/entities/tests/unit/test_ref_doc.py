from contextlib import contextmanager
from unittest.mock import MagicMock, patch

import pytest

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


class TestMarkIngested:
    def test_sets_only_the_is_ingested_flag(self) -> None:
        """`updated_at` carries the source file's timestamp — it feeds asset data versions and the
        default document sort, so marking a document ingested must not touch it."""
        queryset = MagicMock()
        queryset.update_one.return_value = 1

        with patch(_SWITCH_DB, return_value=_switched(queryset)):
            assert RefDoc.mark_ingested(db_alias="my_db", doc_id="doc1") is True

        queryset.update_one.assert_called_once_with(set__data__metadata__is_ingested=True)

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

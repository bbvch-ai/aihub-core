from contextlib import contextmanager
from unittest.mock import MagicMock, patch

import pytest

from swiss_ai_hub.core.persistence.rag.documents.entities.ref_doc import RefDoc

pytestmark = pytest.mark.unit

_SWITCH_DB = "swiss_ai_hub.core.persistence.rag.documents.entities.ref_doc.switch_db"


@contextmanager
def _switched(queryset: MagicMock):
    switched = MagicMock()
    switched.objects.return_value = queryset
    yield switched


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

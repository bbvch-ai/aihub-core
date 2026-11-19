"""What the classification backfill owes each document, and how it writes it (#2483)."""

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from swiss_ai_hub.core.generative_ai import DocumentTypeCatalog, DocumentValueNormalizer
from swiss_ai_hub.core.generative_ai.document.classification.document_classification_answer import (
    DocumentClassificationAnswer,
)
from swiss_ai_hub.core.generative_ai.document.classification.document_type import DocumentType
from swiss_ai_hub.core.persistence import RefDoc
from swiss_ai_hub.core.persistence.rag.documents.entities.ref_doc import DocumentData, Metadata

from swiss_ai_hub.pipeline.services.document_classification_backfill_service import (
    DocumentClassificationBackfillService,
)
from swiss_ai_hub.pipeline.types.backfill_work import BackfillWork

_MODULE = "swiss_ai_hub.pipeline.services.document_classification_backfill_service"
_TEXT = "# Rechnung RE-1\nHooli AG\nZürich, 14. März 2025\nTotal CHF 100.00"


def _ref_doc(doc_id: str, excluded: list[str] | None = None, **metadata: Any) -> RefDoc:
    return RefDoc(
        id=doc_id,
        data=DocumentData(
            metadata=Metadata(
                source=f"s3://kb/finance/{doc_id}.pdf", namespace="finance", content_hash=f"hash-{doc_id}", **metadata
            ),
            excluded_embed_metadata_keys=excluded or [],
        ),
    )


def _current(**overrides: Any) -> dict[str, Any]:
    return {
        "document_type": DocumentType.INVOICE.value,
        "document_classification_version": DocumentTypeCatalog.VERSION,
        "document_type_version": DocumentTypeCatalog.type_definition(DocumentType.INVOICE).version,
        "document_normalizer_version": DocumentValueNormalizer.VERSION,
        **overrides,
    }


def _llm(**copied: Any) -> MagicMock:
    unknown = dict.fromkeys(set(DocumentClassificationAnswer.model_fields) - {"document_type", "secondary_types"})
    answer = DocumentClassificationAnswer(
        **{**unknown, **copied}, document_type=DocumentType.INVOICE, secondary_types=[]
    )
    llm = MagicMock()
    llm.astructured_predict = AsyncMock(return_value=answer)
    return llm


class TestWorkOf:
    @pytest.mark.parametrize(
        ("ref_doc", "work"),
        [
            (_ref_doc("new"), BackfillWork.CLASSIFY),
            (_ref_doc("old", **_current(document_classification_version=0)), BackfillWork.CLASSIFY),
            (_ref_doc("older-type", **_current(document_type_version=0)), BackfillWork.CLASSIFY),
            (_ref_doc("no-type-version", **_current(document_type_version=None)), BackfillWork.CLASSIFY),
            (_ref_doc("parser", **_current(document_normalizer_version=0)), BackfillWork.RENORMALIZE),
            (_ref_doc("done", **_current()), BackfillWork.UP_TO_DATE),
            (_ref_doc("jira", excluded=["issue_type"]), BackfillWork.SYNCED_RECORD),
            (_ref_doc("classified", excluded=["document_type"], **_current()), BackfillWork.UP_TO_DATE),
        ],
        ids=lambda value: value if isinstance(value, str) else None,
    )
    def test_the_work_follows_the_versions_and_frontmatter(self, ref_doc: RefDoc, work: BackfillWork) -> None:
        assert DocumentClassificationBackfillService.work_of(ref_doc) == work


class _Run:
    """The service with every store faked: what it read, what it wrote."""

    def __init__(
        self,
        ref_docs: list[RefDoc],
        *,
        enabled: bool = True,
        deleting: bool = False,
        texts: dict[str, str | None] | None = None,
    ):
        self.ref_docs = ref_docs
        self.enabled = enabled
        self.deleting = deleting
        self.texts = texts or {}
        self.vector_store = MagicMock()
        self.vector_store.rewrite_document_metadata.return_value = {"partition_7": ["n1", "n2"]}
        self.llm = _llm(document_reference_number="RE-1", document_issuer="Hooli AG")
        self.set_classification = MagicMock(return_value=True)

    def backfill(self, dry_run: bool = False):
        with (
            patch(f"{_MODULE}.ensure_main_db_connection"),
            patch(
                f"{_MODULE}.ingestor_config_for_bucket",
                return_value=MagicMock(with_document_classification=self.enabled),
            ),
            patch(
                f"{_MODULE}.BucketEntity.get_bucket_by_bucket_name",
                return_value=MagicMock(db_name="kb", deleting=self.deleting),
            ),
            patch(f"{_MODULE}.MongoConnectionRegistry.ensure_alias"),
            patch.object(RefDoc, "list_classification_states", return_value=self.ref_docs),
            patch.object(RefDoc, "text_of", side_effect=lambda db, doc_id, content_hash: self.texts.get(doc_id, _TEXT)),
            patch.object(RefDoc, "set_classification", self.set_classification),
            patch(f"{_MODULE}.build_vector_store", return_value=self.vector_store),
            patch(f"{_MODULE}.build_language_model", return_value=self.llm) as build_language_model,
        ):
            report = DocumentClassificationBackfillService.backfill(bucket="kb", dry_run=dry_run)
        self.models_built = build_language_model.call_count
        return report


class TestBackfill:
    def test_a_database_that_switched_classification_off_is_left_alone(self) -> None:
        run = _Run([_ref_doc("new")], enabled=False)

        report = run.backfill()

        assert report.disabled
        run.vector_store.rewrite_document_metadata.assert_not_called()

    def test_a_database_being_deleted_is_left_alone(self) -> None:
        run = _Run([_ref_doc("new")], deleting=True)

        report = run.backfill()

        assert report.deleting
        run.vector_store.rewrite_document_metadata.assert_not_called()

    def test_rows_written_for_a_document_that_changed_meanwhile_are_deleted_again(self) -> None:
        """Only the old version's rows were patched; ingestion or removal had replaced or deleted them, so they go."""
        run = _Run([_ref_doc("a")])
        run.set_classification.return_value = False

        report = run.backfill()

        assert report.changed_meanwhile == 1
        run.vector_store.delete_nodes_in_partition.assert_called_once_with(["n1", "n2"], "partition_7")

    def test_a_dry_run_reports_the_work_and_writes_nothing(self) -> None:
        run = _Run([_ref_doc("a"), _ref_doc("b", **_current()), _ref_doc("jira", excluded=["issue_type"])])

        report = run.backfill(dry_run=True)

        assert report.planned == {
            BackfillWork.CLASSIFY: 1,
            BackfillWork.UP_TO_DATE: 1,
            BackfillWork.SYNCED_RECORD: 1,
        }
        run.vector_store.rewrite_document_metadata.assert_not_called()
        run.set_classification.assert_not_called()

    def test_a_document_is_classified_into_its_nodes_first_and_its_record_last(self) -> None:
        run = _Run([_ref_doc("a")])

        report = run.backfill()

        assert report.classified == 1
        document_id, namespace, content_hash, stored, keys = run.vector_store.rewrite_document_metadata.call_args.args
        assert (document_id, namespace, content_hash) == ("a", "finance", "hash-a")
        assert stored["document_type"] == "invoice"
        assert stored["document_issuer"] == "Hooli AG"
        assert keys == DocumentTypeCatalog.metadata_keys()
        run.set_classification.assert_called_once_with("kb", "a", "hash-a", stored, keys)

    def test_every_classification_key_is_written_so_a_changed_type_leaves_nothing_stale(self) -> None:
        run = _Run([_ref_doc("a")])

        run.backfill()

        stored = run.vector_store.rewrite_document_metadata.call_args.args[3]
        assert set(stored) == set(DocumentTypeCatalog.metadata_keys())

    def test_only_a_newer_parser_rereads_the_kept_copies_without_a_model(self) -> None:
        stored = {
            **_current(document_normalizer_version=0),
            "document_type": "invoice",
            "document_types": ["invoice"],
            "document_date_raw": "14. März 2025",
        }
        run = _Run([_ref_doc("a", **stored)])

        report = run.backfill()

        assert report.renormalized == 1
        assert run.models_built == 0
        assert run.vector_store.rewrite_document_metadata.call_args.args[3]["document_date"] == "2025-03-14"

    def test_a_document_reingested_meanwhile_is_left_to_ingestion(self) -> None:
        run = _Run([_ref_doc("a")], texts={"a": None})

        report = run.backfill()

        assert report.changed_meanwhile == 1
        run.vector_store.rewrite_document_metadata.assert_not_called()

    def test_one_failing_document_does_not_stop_the_others(self) -> None:
        run = _Run([_ref_doc("a"), _ref_doc("b")])
        run.vector_store.rewrite_document_metadata.side_effect = [RuntimeError("Milvus"), {"partition_7": ["n1"]}]

        report = run.backfill()

        assert report.failed_document_ids == ["a"]
        assert report.classified == 1

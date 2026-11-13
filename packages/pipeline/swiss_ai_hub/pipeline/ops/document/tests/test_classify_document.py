"""Document classification decides per run whether to work and with which model, and never fails ingestion (#2482)."""

from typing import Any
from unittest.mock import AsyncMock, Mock, patch

from dagster import build_op_context
from swiss_ai_hub.core.generative_ai import DocumentTypeCatalog
from swiss_ai_hub.core.generative_ai.document.classification.document_classification_answer import (
    DocumentClassificationAnswer,
)
from swiss_ai_hub.core.generative_ai.document.classification.document_type import DocumentType

from swiss_ai_hub.pipeline.ops.document.classify_document import classify_document
from swiss_ai_hub.pipeline.resources.parser.document_classification_resource import DocumentClassificationResource
from swiss_ai_hub.pipeline.types.ref_doc_document import RefDocDocument

_MODULE = "swiss_ai_hub.pipeline.ops.document.classify_document"
_PARTITION = "finance|s3:%2F%2Ffinance%2Finvoices%2Fre-1.pdf"
_TEXT = "# Rechnung RE-1\nHooli AG\nZürich, 14. März 2025\nTotal CHF 100.00"


def _config(with_document_classification: bool) -> Mock:
    return Mock(with_document_classification=with_document_classification)


def _ref_doc(**fields: Any) -> RefDocDocument:
    return RefDocDocument(text=_TEXT, id_="doc", metadata={"source": "s3://finance/invoices/re-1.pdf"}, **fields)


def _llm_answering(**values: Any) -> Mock:
    unknown = dict.fromkeys(set(DocumentClassificationAnswer.model_fields) - {"document_type", "secondary_types"})
    answer = DocumentClassificationAnswer(
        **{**unknown, **values}, document_type=DocumentType.INVOICE, secondary_types=[]
    )
    llm = Mock()
    llm.astructured_predict = AsyncMock(return_value=answer)
    return llm


def _classify(
    ref_doc: RefDocDocument, resource: Any, *, opted_in: bool = True, llm: Any = None
) -> tuple[RefDocDocument, list[str]]:
    """The op's output, and the buckets whose language model it built."""
    with (
        patch(f"{_MODULE}.ingestor_config_for_bucket", return_value=_config(opted_in)),
        patch(f"{_MODULE}.build_language_model", return_value=llm or Mock()) as build_language_model,
    ):
        result = classify_document(build_op_context(partition_key=_PARTITION), ref_doc, resource)
    return result.value, [call.args[0] for call in build_language_model.call_args_list]


class TestClassifyDocument:
    def test_a_database_that_opted_out_gets_its_document_back_untouched(self) -> None:
        resource = Mock()

        result, _ = _classify(_ref_doc(), resource, opted_in=False)

        assert result.metadata == {"source": "s3://finance/invoices/re-1.pdf"}
        resource.classify.assert_not_called()

    def test_a_record_synced_with_its_own_fields_is_not_classified(self) -> None:
        resource = Mock()

        result, _ = _classify(_ref_doc(excluded_embed_metadata_keys=["issue_type"]), resource)

        assert "document_type" not in result.metadata
        resource.classify.assert_not_called()

    def test_a_document_is_classified_with_its_own_databases_text_model(self) -> None:
        llm = _llm_answering(document_reference_number="RE-1", document_issuer="Hooli AG")

        result, built_for = _classify(_ref_doc(), DocumentClassificationResource(), llm=llm)

        assert built_for == ["finance"]
        assert result.metadata["document_type"] == "invoice"
        assert result.metadata["document_reference_number"] == "RE-1"
        assert result.metadata["document_issuer"] == "Hooli AG"
        assert result.metadata["source"] == "s3://finance/invoices/re-1.pdf"
        assert result.text == _TEXT

    def test_classification_stays_out_of_the_embedded_and_model_facing_text(self) -> None:
        """Filter metadata, not content: embeddings must not change, so a backfill never embeds again."""
        result, _ = _classify(
            _ref_doc(), DocumentClassificationResource(), llm=_llm_answering(document_issuer="Hooli AG")
        )

        assert set(DocumentTypeCatalog.metadata_keys()) <= set(result.excluded_embed_metadata_keys)
        assert set(DocumentTypeCatalog.metadata_keys()) <= set(result.excluded_llm_metadata_keys)
        embedded = result.get_content(metadata_mode="embed")
        assert "document_type" not in embedded
        assert "document_issuer" not in embedded

    def test_a_failed_call_leaves_the_document_unclassified_instead_of_failing_ingestion(self) -> None:
        llm = Mock()
        llm.astructured_predict = AsyncMock(side_effect=ValueError("not JSON"))

        result, _ = _classify(_ref_doc(), DocumentClassificationResource(), llm=llm)

        assert result.metadata == {"source": "s3://finance/invoices/re-1.pdf"}
        assert result.excluded_embed_metadata_keys == []

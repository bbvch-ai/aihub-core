import logging
from functools import cache
from typing import Annotated, Any

from llama_index.core.llms import LLM
from swiss_ai_hub.core.generative_ai import (
    DocumentClassification,
    DocumentClassifier,
    DocumentTypeCatalog,
    DocumentValueNormalizer,
)
from swiss_ai_hub.core.infrastructure import MongoConnectionRegistry
from swiss_ai_hub.core.persistence import (
    DOCUMENT_CLASSIFICATION_VERSION,
    DOCUMENT_NORMALIZER_VERSION,
    DOCUMENT_TITLE,
    HASH,
    NAMESPACE,
    SOURCE,
    BucketEntity,
    PartitionAwareMilvusVectorStore,
    RefDoc,
)

from swiss_ai_hub.pipeline.types.backfill_work import BackfillWork
from swiss_ai_hub.pipeline.types.document_classification_backfill_report import DocumentClassificationBackfillReport
from swiss_ai_hub.pipeline.util.async_utils import run_async
from swiss_ai_hub.pipeline.util.bucket_utils import ensure_main_db_connection
from swiss_ai_hub.pipeline.util.model_builders import build_language_model, ingestor_config_for_bucket
from swiss_ai_hub.pipeline.util.store_builders import build_vector_store

logger = logging.getLogger(__name__)


class DocumentClassificationBackfillService:
    """Classifies the documents a database ingested before classification, from their stored text (#2483).

    Nothing is parsed or embedded again. A document is classified with the database's text model when it has no
    classification or one of an older `DocumentTypeCatalog.VERSION`; when only `DocumentValueNormalizer.VERSION` is
    newer, its kept copies are read again without a model. Records synced with frontmatter are left alone, as at
    ingestion.

    Each document's nodes are written before its record, and the record only while its content is the one read: the
    record's versions are what marks a document done, so a failure leaves it owed. Only nodes of the version read are
    patched (they carry its content hash), and when the record write finds the document changed or removed meanwhile,
    the rows just written are deleted again: a re-ingested document is left to ingestion, which classifies it itself,
    and no deleted node comes back. A removal that deletes the nodes and has not yet deleted the record while this
    runs can still leave rows behind, which `{ingestor}_repair_orphaned_nodes` removes. A database being deleted is
    not touched. A document that fails is counted and the run goes on;
    only infrastructure errors fail the run.
    """

    @classmethod
    def backfill(
        cls,
        bucket: Annotated[str, "S3 bucket backing the knowledge database"],
        dry_run: Annotated[bool, "Report the work without doing it"],
    ) -> DocumentClassificationBackfillReport:
        ensure_main_db_connection()
        report = DocumentClassificationBackfillReport(dry_run=dry_run)
        if not ingestor_config_for_bucket(bucket).with_document_classification:
            report.disabled = True
            return report

        bucket_entity = BucketEntity.get_bucket_by_bucket_name(bucket)
        if bucket_entity.deleting:
            report.deleting = True
            return report
        db_name = bucket_entity.db_name
        MongoConnectionRegistry.ensure_alias(db_name)
        plan = [(ref_doc, cls.work_of(ref_doc)) for ref_doc in RefDoc.list_classification_states(db_name)]
        report.plan([work for _, work in plan])
        if dry_run:
            return report

        vector_store = build_vector_store(db_name)
        llm = cache(lambda: build_language_model(bucket))
        for ref_doc, work in plan:
            if work in (BackfillWork.CLASSIFY, BackfillWork.RENORMALIZE):
                cls._backfill_one(ref_doc, work, db_name, vector_store, llm, report)
        return report

    @classmethod
    def work_of(cls, ref_doc: RefDoc) -> BackfillWork:
        """What the document is owed, from the keys frontmatter excluded and the versions it was classified with."""
        metadata = cls._metadata(ref_doc)
        excluded = set(ref_doc.data.excluded_embed_metadata_keys or [])
        if excluded - set(DocumentTypeCatalog.metadata_keys()):
            return BackfillWork.SYNCED_RECORD
        classification_version = metadata.get(DOCUMENT_CLASSIFICATION_VERSION)
        if classification_version is None or classification_version < DocumentTypeCatalog.VERSION:
            return BackfillWork.CLASSIFY
        if (metadata.get(DOCUMENT_NORMALIZER_VERSION) or 0) < DocumentValueNormalizer.VERSION:
            return BackfillWork.RENORMALIZE
        return BackfillWork.UP_TO_DATE

    @classmethod
    def _backfill_one(
        cls,
        ref_doc: RefDoc,
        work: BackfillWork,
        db_name: str,
        vector_store: PartitionAwareMilvusVectorStore,
        llm: Any,
        report: DocumentClassificationBackfillReport,
    ) -> None:
        document_id = str(ref_doc.id)
        try:
            written = cls._write(ref_doc, work, db_name, vector_store, llm)
        except Exception:  # noqa: BLE001 - one document must not stop the others; it stays owed for the next run
            logger.warning(f"Backfilling document {document_id} of '{db_name}' failed", exc_info=True)
            report.failed_document_ids.append(document_id)
            return
        if not written:
            report.changed_meanwhile += 1
        elif work is BackfillWork.CLASSIFY:
            report.classified += 1
        else:
            report.renormalized += 1

    @classmethod
    def _write(
        cls, ref_doc: RefDoc, work: BackfillWork, db_name: str, vector_store: PartitionAwareMilvusVectorStore, llm: Any
    ) -> bool:
        """Classify one document and store it; False when its content changed or it was removed since listing."""
        metadata = cls._metadata(ref_doc)
        content_hash = metadata[HASH]
        text = RefDoc.text_of(db_name, str(ref_doc.id), content_hash)
        if text is None:
            return False
        classification = (
            cls._classify(text, metadata, llm())
            if work is BackfillWork.CLASSIFY
            else DocumentClassification.renormalized(metadata, text)
        )
        keys = DocumentTypeCatalog.metadata_keys()
        # A key the new classification does not write is cleared, so a document whose type changed keeps no stale
        # value from the old one.
        stored = {**dict.fromkeys(keys), **classification.to_metadata()}
        document_id = str(ref_doc.id)
        rewritten = vector_store.rewrite_document_metadata(document_id, metadata[NAMESPACE], content_hash, stored, keys)
        if RefDoc.set_classification(db_name, document_id, content_hash, stored, keys):
            return True
        # Changed or removed since the text was read: the rows just written can only be the old version's, which
        # ingestion or removal had replaced or deleted meanwhile, so they go.
        for partition_name, node_ids in rewritten.items():
            vector_store.delete_nodes_in_partition(node_ids, partition_name)
        return False

    @staticmethod
    def _classify(text: str, metadata: dict[str, Any], llm: LLM) -> DocumentClassification:
        title = metadata.get(DOCUMENT_TITLE) or str(metadata.get(SOURCE, "")).rsplit("/", 1)[-1]
        return run_async(DocumentClassifier.classify(text, title, llm))

    @staticmethod
    def _metadata(ref_doc: RefDoc) -> dict[str, Any]:
        return ref_doc.data.metadata.to_mongo().to_dict() if ref_doc.data.metadata else {}

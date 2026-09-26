import logging
from typing import Annotated

from llama_index.core.utils import iter_batch
from swiss_ai_hub.core.infrastructure import MongoConnectionRegistry
from swiss_ai_hub.core.persistence import BucketEntity, NamespaceEntity, PartitionAwareMilvusVectorStore, RefDoc

from swiss_ai_hub.pipeline.types.data_lake_file import DataLakeFile
from swiss_ai_hub.pipeline.types.orphaned_node_repair_report import OrphanedNodeRepairReport
from swiss_ai_hub.pipeline.util.bucket_utils import ensure_main_db_connection
from swiss_ai_hub.pipeline.util.store_builders import build_s3_data_lake_client, build_vector_store

logger = logging.getLogger(__name__)

RECHECKED_DOCUMENTS_PER_DELETE = 500


class OrphanedNodeRepairService:
    """Deletes vector nodes whose document has neither a doc store record nor a file in the data lake.

    Removals used to delete the record before the vectors, so a failed vector delete stranded the nodes with
    nothing left to retry from (#1925). Ingestion writes a document's record before its nodes, so a node
    without a record is an orphan. Files in the data lake are kept too, to protect a document between
    landing and record creation.
    """

    @classmethod
    def repair(
        cls,
        bucket: Annotated[str, "S3 bucket backing the knowledge database"],
        dry_run: Annotated[bool, "Report the orphans without deleting them"],
    ) -> OrphanedNodeRepairReport:
        ensure_main_db_connection()
        bucket_entity = BucketEntity.get_bucket_by_bucket_name(bucket)
        db_name = bucket_entity.db_name
        MongoConnectionRegistry.ensure_alias(db_name)

        data_lake_files = build_s3_data_lake_client(bucket).get_all_files()
        keep_ids = RefDoc.get_all_ids(db_name) | {data_lake_file.id_ for data_lake_file in data_lake_files}
        namespaces = cls._namespaces(str(bucket_entity.id), db_name, data_lake_files)

        vector_store = build_vector_store(db_name)
        report = OrphanedNodeRepairReport(dry_run=dry_run)
        for partition_name in vector_store.document_partition_names(namespaces):
            orphans = {
                document_id: node_ids
                for document_id, node_ids in vector_store.node_ids_by_document(partition_name).items()
                if document_id not in keep_ids
            }
            report.add_orphans(orphans)
            logger.info(f"Found {len(orphans)} orphaned documents in partition '{partition_name}' of '{db_name}'")
            if not dry_run:
                report.deleted_nodes += cls._delete_orphans(vector_store, db_name, partition_name, orphans)
        return report

    @staticmethod
    def _namespaces(bucket_id: str, db_name: str, data_lake_files: list[DataLakeFile]) -> list[str]:
        """Every namespace the database may have written nodes for, whether or not it still has documents."""
        registered = [namespace.namespace_name for namespace in NamespaceEntity.get_namespaces_by_bucket(bucket_id)]
        in_data_lake = [data_lake_file.namespace for data_lake_file in data_lake_files]
        return sorted({*registered, *RefDoc.get_all_namespaces(db_name), *in_data_lake})

    @staticmethod
    def _delete_orphans(
        vector_store: PartitionAwareMilvusVectorStore,
        db_name: str,
        partition_name: str,
        orphans: dict[str, list[str]],
    ) -> int:
        """Delete by the scanned primary keys only, so nodes written after the scan are never touched.

        Each batch re-checks the records first: a re-ingest may have recreated a document since the keep set
        was read.
        """
        deleted = 0
        for document_ids in iter_batch(list(orphans), RECHECKED_DOCUMENTS_PER_DELETE):
            recreated = RefDoc.get_existing_ids(db_name, document_ids)
            if recreated:
                logger.info(f"Keeping {len(recreated)} documents recreated since the scan: {sorted(recreated)}")
            node_ids = [
                node_id
                for document_id in document_ids
                if document_id not in recreated
                for node_id in orphans[document_id]
            ]
            deleted += vector_store.delete_nodes_in_partition(node_ids, partition_name)
        return deleted

from typing import Annotated

from swiss_ai_hub.core.persistence import PartitionAwareMilvusVectorStore, StoredNodeKey

from swiss_ai_hub.pipeline.types.default_partition_repair_report import DefaultPartitionRepairReport
from swiss_ai_hub.pipeline.util.bucket_utils import get_db_name_from_bucket_name
from swiss_ai_hub.pipeline.util.model_builders import embedding_dimension_for_bucket
from swiss_ai_hub.pipeline.util.store_builders import build_vector_store


class DefaultPartitionRepairService:
    """Provisions a database's vector collection and moves nodes stranded in ``_default`` to where readers look.

    Creating a collection's 1023 partitions takes 15-25 s. A process that opened it meanwhile took it for an
    unpartitioned one and wrote to ``_default``, which readers scoped to a namespace never search (#1923). Running
    this before an observation registers any document means no ingestion run meets a missing or half-built
    collection, and the collection is created with the width of the database's own embedding model.

    Stranded nodes are copied as stored, so nothing is parsed or embedded again. A document's nodes of one type move
    as a unit, copied and flushed before they are deleted from ``_default``: an interruption leaves duplicates, which
    the next run deletes, never a gap. Node ids are fresh uuids per ingestion, so a node id in the namespace partition
    that ``_default`` lacks means a later ingestion superseded the stranded copies, which are then deleted instead.
    """

    @classmethod
    def repair(cls, bucket: Annotated[str, "S3 bucket backing the knowledge database"]) -> DefaultPartitionRepairReport:
        vector_store = build_vector_store(get_db_name_from_bucket_name(bucket), embedding_dimension_for_bucket(bucket))
        report = DefaultPartitionRepairReport(partition_state=vector_store.ensure_partitions())
        for (namespace, document_id), stranded_by_type in cls._by_document(vector_store.stranded_nodes()).items():
            cls._repair_document(vector_store, namespace, document_id, stranded_by_type, report)
        return report

    @staticmethod
    def _by_document(nodes: list[StoredNodeKey]) -> dict[tuple[str, str], dict[str | None, list[str]]]:
        by_document: dict[tuple[str, str], dict[str | None, list[str]]] = {}
        for node in nodes:
            by_type = by_document.setdefault((node.namespace, node.document_id), {})
            by_type.setdefault(node.node_type, []).append(node.node_id)
        return by_document

    @staticmethod
    def _repair_document(
        vector_store: PartitionAwareMilvusVectorStore,
        namespace: str,
        document_id: str,
        stranded_by_type: dict[str | None, list[str]],
        report: DefaultPartitionRepairReport,
    ) -> None:
        present = vector_store.node_keys_of_document(document_id, namespace)
        for node_type, stranded_ids in stranded_by_type.items():
            present_ids = {node.node_id for node in present if node.node_type == node_type}
            if present_ids - set(stranded_ids):
                report.superseded_nodes += vector_store.delete_stranded_nodes(stranded_ids)
                continue

            missing_ids = [node_id for node_id in stranded_ids if node_id not in present_ids]
            if missing_ids:
                report.moved_nodes += vector_store.restore_stranded_nodes(missing_ids, namespace)
            vector_store.delete_stranded_nodes(stranded_ids)
        report.document_ids.append(document_id)

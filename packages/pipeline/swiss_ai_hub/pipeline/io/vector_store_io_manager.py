import time
from datetime import datetime, timedelta

from dagster import ConfigurableIOManager, InputContext, OutputContext
from llama_index.core.schema import TextNode
from llama_index.core.vector_stores.types import BasePydanticVectorStore, MetadataFilter, MetadataFilters
from swiss_ai_hub.core.persistence.rag.vectors.node_metadata import DOCUMENT_ID

from swiss_ai_hub.pipeline.io.ingestion_marking import mark_ref_docs_as_ingested
from swiss_ai_hub.pipeline.util.bucket_utils import get_db_name_from_bucket_name
from swiss_ai_hub.pipeline.util.id_utils import uri_to_id
from swiss_ai_hub.pipeline.util.model_builders import embedding_dimension_for_bucket
from swiss_ai_hub.pipeline.util.partition_utils import split_composite_partition_key
from swiss_ai_hub.pipeline.util.run_routing import bucket_from_run_tag
from swiss_ai_hub.pipeline.util.store_builders import build_vector_store

_MAX_RETRY_SECONDS = 30
_RETRY_INTERVAL_SECONDS = 1


class VectorStoreIOManager(ConfigurableIOManager):
    """Milvus vector store IO manager for the document ingestion pipeline, routed per run by bucket.

    Partition keys are composite ``{bucket}|{file_uri}``: the collection is resolved from the ``bucket``
    component and the document id from the decoded file URI. Keeps the upsert + eventual-consistency retry
    behaviour of ``VectorStoreIOManager`` so re-observes upsert over ``uri_to_id`` ids within their bucket's
    collection. The non-partitioned branch (unused by the standard graph) resolves the bucket from the
    ``aihub/bucket`` run tag for parity.

    A document counts as ingested only once its nodes are in Milvus, so the ``is_ingested`` flip happens
    here, right after the write — the same contract the non-routed manager holds.
    """

    encode_partition_keys: bool = True
    document_id_key: str = DOCUMENT_ID

    def handle_output(self, context: OutputContext, obj: list[TextNode] | list[list[TextNode]]) -> None:
        if obj and isinstance(obj[0], list):
            nodes = [node for sublist in obj for node in sublist]
        else:
            nodes = obj
        if not nodes:
            context.log.warning("No nodes to add to vector store")
            return
        bucket, _ = split_composite_partition_key(context.partition_key, encode=self.encode_partition_keys)
        db_name = get_db_name_from_bucket_name(bucket)
        build_vector_store(db_name, embedding_dimension_for_bucket(bucket)).add(nodes)
        context.log.info(f"Successfully added {len(nodes)} nodes to vector store '{bucket}'")
        mark_ref_docs_as_ingested(nodes, db_name, context.log, self.document_id_key)

    def load_input(self, context: InputContext) -> list[TextNode] | list[list[TextNode]]:
        if context.has_partition_key:
            bucket, file_uri = split_composite_partition_key(context.partition_key, encode=self.encode_partition_keys)
            return self._query_single(self._store_for_bucket(bucket), uri_to_id(file_uri), context)

        bucket = bucket_from_run_tag(context)
        store = self._store_for_bucket(bucket)
        bucket_prefix = f"{bucket}|"
        partitions_def = context.upstream_output.asset_partitions_def
        if partitions_def is None:
            raise ValueError("Cannot load nodes without partition information.")
        all_partition_keys = partitions_def.get_partition_keys(dynamic_partitions_store=context.instance)
        return [
            self._query_single(
                store, uri_to_id(split_composite_partition_key(key, encode=self.encode_partition_keys)[1]), context
            )
            for key in all_partition_keys
            if key.startswith(bucket_prefix)
        ]

    @staticmethod
    def _store_for_bucket(bucket: str) -> BasePydanticVectorStore:
        return build_vector_store(get_db_name_from_bucket_name(bucket))

    def _query_single(self, store: BasePydanticVectorStore, doc_id: str, context: InputContext) -> list[TextNode]:
        filters = MetadataFilters(filters=[MetadataFilter(key=self.document_id_key, value=doc_id)])
        context.log.info(f"Querying vector store for document ID: {doc_id}")

        end_time = datetime.now() + timedelta(seconds=_MAX_RETRY_SECONDS)
        while datetime.now() < end_time:
            nodes = store.get_nodes(filters=filters)
            if nodes:
                context.log.info(f"Found {len(nodes)} nodes for document {doc_id}")
                return nodes
            context.log.info(f"No nodes found for document {doc_id}. Retrying in {_RETRY_INTERVAL_SECONDS}s...")
            time.sleep(_RETRY_INTERVAL_SECONDS)

        context.log.warning(f"No nodes found for document {doc_id} after {_MAX_RETRY_SECONDS}s")
        return []

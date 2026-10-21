import json
from collections.abc import Iterator
from typing import Any

from llama_index.core.schema import BaseNode, NodeRelationship
from llama_index.core.utils import iter_batch
from llama_index.core.vector_stores import MetadataFilters
from llama_index.core.vector_stores.types import VectorStoreQuery, VectorStoreQueryMode, VectorStoreQueryResult
from llama_index.core.vector_stores.utils import node_to_metadata_dict
from llama_index.vector_stores.milvus import MilvusVectorStore
from llama_index.vector_stores.milvus.utils import BaseSparseEmbeddingFunction
from pymilvus import MilvusClient

from swiss_ai_hub.core.persistence.rag.vectors.node_metadata import DOCUMENT_ID, NAMESPACE
from swiss_ai_hub.core.persistence.rag.vectors.stores.milvus_partition_manager import (
    DEFAULT_PARTITION_NAME,
    MANUAL_PARTITION_PREFIX,
    MANUAL_PARTITIONS_MARKER,
    MAX_PARTITIONS,
    create_manual_partitions,
    get_partition_name_for_namespace,
    get_partition_names_for_namespaces,
)
from swiss_ai_hub.core.persistence.rag.vectors.stores.milvus_partition_state import MilvusPartitionState
from swiss_ai_hub.core.persistence.rag.vectors.stores.stored_node_key import StoredNodeKey

try:
    from pymilvus import AnnSearchRequest, RRFRanker, WeightedRanker
except ImportError:
    AnnSearchRequest = None
    RRFRanker = None
    WeightedRanker = None

MILVUS_DYNAMIC_FIELD_MAX_BYTES = 65536
DOCUMENT_IDS_PER_DELETE_EXPRESSION = 500
NODE_IDS_PER_DELETE = 1000
NODES_PER_SCAN_PAGE = 1000


class PartitionAwareMilvusVectorStore(MilvusVectorStore):
    """
    Memory-efficient Milvus store that loads only queried partitions based on namespace.

    Accepts a pre-configured MilvusClient for dependency injection, enabling
    connection reuse across the application and proper health checking.

    Limitations:
    - Copies insertion logic from base class (LlamaIndex doesn't support partition injection)
    - Overrides HYBRID search (base class doesn't forward kwargs to _hybrid_search)

    If LlamaIndex adds partition parameter support, simplify to:
    - add(): Just set partition_name= per batch
    - query(): Just set partition_names= in kwargs

    The layout is read per collection (see ``partition_state``). A legacy collection, created before manual partitions
    and without the creation marker, keeps everything in ``_default`` and goes through the base class. A half-built
    one — partitions still being created, or a creator that died mid-way (#1923) — is completed before any write, so
    a partitioned collection never receives new nodes in ``_default``.
    """

    def __init__(
        self,
        client: MilvusClient,
        uri: str,
        token: str | None = None,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """
        Initialize with a pre-configured MilvusClient.

        LlamaIndex's MilvusVectorStore creates its own internal clients. We pass uri/token
        to satisfy the parent, then override with our pre-configured client for actual operations.
        This enables connection reuse and proper health checking.
        """
        # Pass uri/token to parent so it doesn't use the default './milvus_llamaindex.db'
        super().__init__(uri=uri, token=token or "", *args, **kwargs)

        # Override the parent's internally-created client with our pre-configured one
        self._milvusclient = client

        self._settled_partition_state: MilvusPartitionState | None = None
        self._collection_description: dict[str, Any] | None = None

    def _ensure_collection_loaded(self, partition_names: list[str] | None = None) -> None:
        """Lazily load partitions (or whole collection if none specified). Idempotent — blocks until ready.

        Loading the full collection on a 1023-partition store is ~54 GB and will not fit
        in a typical query-node memory budget; always pass partition_names when known.
        Memory eviction of unused partitions is handled by Milvus itself.
        """
        if partition_names:
            self.client.load_partitions(
                collection_name=self.collection_name,
                partition_names=partition_names,
            )
        else:
            self.client.load_collection(collection_name=self.collection_name)

    def partition_state(self) -> MilvusPartitionState:
        """How this collection lays out its nodes.

        Only a settled state is cached. Pipeline stores live for the whole process, and caching a half-built
        collection as unpartitioned is what sent every later write of that process into ``_default`` (#1923).
        """
        if self._settled_partition_state is not None:
            return self._settled_partition_state

        state = self._partition_state_of(self._manual_partition_names())
        if state is not MilvusPartitionState.PARTIAL:
            self._settled_partition_state = state
        return state

    def _partition_state_of(self, manual_partition_names: set[str]) -> MilvusPartitionState:
        if len(manual_partition_names) == MAX_PARTITIONS:
            return MilvusPartitionState.COMPLETE
        if not manual_partition_names and self._described_collection().get("description") != MANUAL_PARTITIONS_MARKER:
            return MilvusPartitionState.LEGACY
        return MilvusPartitionState.PARTIAL

    def _manual_partition_names(self) -> set[str]:
        partitions = self.client.list_partitions(collection_name=self.collection_name)
        return {name for name in partitions if name.startswith(MANUAL_PARTITION_PREFIX)}

    def ensure_partitions(self) -> MilvusPartitionState:
        """Complete a half-built collection; returns the resulting state.

        A legacy collection is left as it is: it has no partitions to complete, and converting it is a migration of
        every node it holds, not a repair.
        """
        if self.partition_state() is MilvusPartitionState.PARTIAL:
            create_manual_partitions(client=self.client, collection_name=self.collection_name)
        return self.partition_state()

    def add(self, nodes: list[BaseNode], **add_kwargs: Any) -> list[str]:
        """
        Insert nodes into their hashed partitions, completing a half-built collection first; a legacy collection
        falls back to the base class, which writes to ``_default``.

        Sanitize and verify every node before writing any of them: a batch spans namespaces and is inserted
        one partition at a time, so validating at the insert site would leave earlier partitions written
        behind a rejected one. Verifying here also covers the super().add() fallback, which builds its own
        entries. Re-deriving the entry costs one node_to_metadata_dict per node, negligible against embedding.
        """
        if not nodes:
            return []

        nodes = [self._without_child_relationship(node) for node in nodes]
        for node in nodes:
            self._verify_entry_fits(node_to_metadata_dict(node, remove_text=True, text_field=self.text_key), node)

        state = self.ensure_partitions()
        if state is MilvusPartitionState.LEGACY:
            self._ensure_collection_loaded()
            return super().add(nodes, **add_kwargs)
        if state is MilvusPartitionState.PARTIAL:
            raise RuntimeError(f"Collection {self.collection_name} is still missing manual partitions after completion")

        by_namespace = self._group_nodes_by_namespace(nodes)
        partition_names = [get_partition_name_for_namespace(ns) for ns in by_namespace]
        self._ensure_collection_loaded(partition_names=partition_names)

        all_ids: list[str] = []
        for namespace, ns_nodes in by_namespace.items():
            partition_name = get_partition_name_for_namespace(namespace)
            all_ids.extend(self._insert_nodes_to_partition(ns_nodes, partition_name))

        if add_kwargs.get("force_flush", False):
            self.client.flush(self.collection_name)

        return all_ids

    @staticmethod
    def _without_child_relationship(node: BaseNode) -> BaseNode:
        """
        Drop parent -> children before serialization: node_to_metadata_dict packs relationships into the
        dynamic field, which Milvus caps at 65536 bytes, and a hierarchical summary node carries one entry
        per descendant — unbounded. The edge is not lost, since every child persists its own parent edge and
        this is that edge's exact inverse; recovering it means scanning the document's nodes, as it is inside
        the _node_content JSON string rather than a queryable key.

        Returns a copy: the caller's nodes continue to downstream ops, so writing them must not change them.
        """
        if NodeRelationship.CHILD not in node.relationships:
            return node

        relationships = {
            relationship: info
            for relationship, info in node.relationships.items()
            if relationship != NodeRelationship.CHILD
        }
        return node.model_copy(update={"relationships": relationships})

    def _described_collection(self) -> dict[str, Any]:
        """The schema never changes after creation, so one describe_collection serves the store's lifetime."""
        if self._collection_description is None:
            self._collection_description = self.client.describe_collection(collection_name=self.collection_name)

        return self._collection_description

    def _declared_field_names(self) -> set[str]:
        """
        Resolve declared columns from the live collection rather than restating the schema, which lives in
        milvus_vector_store_factory and would drift. The store attributes alone are not enough either —
        namespace is a declared column with no corresponding attribute.
        """
        return {field["name"] for field in self._described_collection()["fields"]}

    def _verify_entry_fits(self, entry: dict[str, Any], node: BaseNode) -> None:
        """Split declared columns from the dynamic remainder exactly as pymilvus does before packing it."""
        declared_fields = self._declared_field_names()
        dynamic_field = {key: value for key, value in entry.items() if key not in declared_fields}
        self._verify_dynamic_field_fits(dynamic_field, node)

    @classmethod
    def _verify_dynamic_field_fits(cls, dynamic_field: dict[str, Any], node: BaseNode) -> None:
        """Fail with a diagnosable message instead of Milvus' code=1100, which names neither the document
        nor the node."""
        size = cls._json_size_in_bytes(dynamic_field)
        if size <= MILVUS_DYNAMIC_FIELD_MAX_BYTES:
            return

        by_size = sorted(dynamic_field, key=lambda key: cls._json_size_in_bytes(dynamic_field[key]), reverse=True)
        largest_keys = [f"{key}={cls._json_size_in_bytes(dynamic_field[key])}B" for key in by_size[:3]]
        raise ValueError(
            f"Node {node.node_id} of document {node.metadata.get(DOCUMENT_ID)} serializes to {size} bytes of "
            f"Milvus dynamic field, over the {MILVUS_DYNAMIC_FIELD_MAX_BYTES} limit. "
            f"Largest keys: {largest_keys}"
        )

    @staticmethod
    def _json_size_in_bytes(value: Any) -> int:
        """
        Mirror how pymilvus packs the dynamic field: orjson.dumps, which emits compact separators and raw
        UTF-8. Milvus then measures the result in bytes, which diverges from character count on the very
        German documents most likely to breach the limit.
        """
        return len(json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode())

    @staticmethod
    def _group_nodes_by_namespace(nodes: list[BaseNode]) -> dict[str, list[BaseNode]]:
        """Group nodes by namespace for partition routing."""
        by_namespace: dict[str, list[BaseNode]] = {}
        for node in nodes:
            namespace = node.metadata.get(NAMESPACE, "")
            by_namespace.setdefault(namespace, []).append(node)
        return by_namespace

    def _insert_nodes_to_partition(self, nodes: list[BaseNode], partition_name: str) -> list[str]:
        """
        Insert nodes to specific partition.

        This duplicates base class logic because LlamaIndex doesn't expose
        partition_name parameter in add(). If LlamaIndex adds support, remove this method.
        """
        insert_list = []
        insert_ids = []

        for node in nodes:
            entry = node_to_metadata_dict(node, remove_text=True, text_field=self.text_key)
            entry[self.text_key] = node.dict()[self.text_key]
            entry["id"] = node.node_id

            if self.enable_dense:
                entry[self.embedding_field] = node.embedding

            if self.enable_sparse:
                if isinstance(self.sparse_embedding_function, BaseSparseEmbeddingFunction):
                    entry[self.sparse_embedding_field] = self.sparse_embedding_function.encode_documents([node.text])[0]

            insert_ids.append(node.node_id)
            insert_list.append(entry)

        executor = self.client.upsert if self.upsert_mode else self.client.insert
        for batch in iter_batch(insert_list, self.batch_size):
            executor(collection_name=self.collection_name, data=batch, partition_name=partition_name)

        return insert_ids

    def query(self, query: VectorStoreQuery, **kwargs: Any) -> VectorStoreQueryResult:
        """
        Query only partitions containing target namespaces.

        Limitations:
        - Copies insertion logic from base class (LlamaIndex doesn't support partition injection)
        - Overrides HYBRID search (base class doesn't forward kwargs)

        If LlamaIndex adds partition parameter support, simplify to:

        - add(): Just set partition_name= per batch
        - query(): Just set partition_names= in kwargs
        """
        if self.partition_state() is MilvusPartitionState.LEGACY:
            self._ensure_collection_loaded()
            return super().query(query, **kwargs)

        namespaces = self._extract_namespaces_from_query(query)
        partition_names: list[str] | None = None
        if namespaces:
            partition_names = self.document_partition_names(namespaces)
            kwargs["milvus_partition_names"] = partition_names

        self._ensure_collection_loaded(partition_names=partition_names)

        # HYBRID mode workaround: base class doesn't pass kwargs, so handle it ourselves
        if query.mode == VectorStoreQueryMode.HYBRID:
            return self._query_hybrid_mode(query, **kwargs)

        # All other modes work correctly with base class
        return super().query(query, **kwargs)

    def _query_hybrid_mode(self, query: VectorStoreQuery, **kwargs: Any) -> VectorStoreQueryResult:
        """
        Handle HYBRID mode with partition support.

        This workaround exists because base class doesn't forward kwargs to _hybrid_search().
        If LlamaIndex fixes this, remove this method.
        """
        filter_string_expr, output_fields = self._prepare_before_search(query, **kwargs)
        custom_string_expr = kwargs.pop("string_expr", "")
        string_expr = filter_string_expr if filter_string_expr else custom_string_expr

        nodes, similarities, ids = self._hybrid_search(query, string_expr, output_fields, **kwargs)
        return VectorStoreQueryResult(nodes=nodes, similarities=similarities, ids=ids)

    def _extract_namespaces_from_query(self, query: VectorStoreQuery) -> list[str]:
        """Extract namespace values from query filters (handles 2-level nesting)."""
        if not query.filters or not hasattr(query.filters, "filters"):
            return []
        return self._extract_namespaces_from_metadata_filters(query.filters)

    def _extract_namespaces_from_metadata_filters(self, filters: MetadataFilters) -> list[str]:
        namespaces: list[str] = []
        for filter_item in filters.filters:
            if self._is_namespace_filter(filter_item):
                namespaces.append(filter_item.value)
            elif hasattr(filter_item, "filters"):
                for nested in filter_item.filters:
                    if self._is_namespace_filter(nested):
                        namespaces.append(nested.value)
        return namespaces

    @staticmethod
    def _is_namespace_filter(filter_item: Any) -> bool:
        """Check if filter item is a namespace filter with string value."""
        return (
            hasattr(filter_item, "key")
            and filter_item.key == NAMESPACE
            and hasattr(filter_item, "value")
            and isinstance(filter_item.value, str)
        )

    def _hybrid_search(
        self, query: VectorStoreQuery, string_expr: str, output_fields: list[str], **kwargs: Any
    ) -> tuple[list[BaseNode], list[float], list[str]]:
        """
        Override hybrid search to support partition_names.

        This duplicates base class logic because base class doesn't accept partition_names.
        If LlamaIndex adds partition_names support, remove this method.
        """
        if isinstance(self.sparse_embedding_function, BaseSparseEmbeddingFunction):
            sparse_emb = self.sparse_embedding_function.encode_queries([query.query_str])[0]
            query_data = [sparse_emb]
            sparse_metric_type = "IP"
        else:
            query_data = [query.query_str]
            sparse_metric_type = "BM25"

        sparse_req = AnnSearchRequest(
            data=query_data,
            anns_field=self.sparse_embedding_field,
            param={"metric_type": sparse_metric_type},
            limit=query.similarity_top_k,
            expr=string_expr,
        )
        dense_search_params = {
            "metric_type": self.similarity_metric,
            "params": self.search_config,
        }
        dense_req = AnnSearchRequest(
            data=[query.query_embedding],
            anns_field=self.embedding_field,
            param=dense_search_params,
            limit=query.similarity_top_k,
            expr=string_expr,
        )

        if self.hybrid_ranker == "WeightedRanker":
            if self.hybrid_ranker_params == {}:
                self.hybrid_ranker_params = {"weights": [1.0, 1.0]}
            ranker = WeightedRanker(*self.hybrid_ranker_params["weights"])
        elif self.hybrid_ranker == "RRFRanker":
            if self.hybrid_ranker_params == {}:
                self.hybrid_ranker_params = {"k": 60}
            ranker = RRFRanker(self.hybrid_ranker_params["k"])
        else:
            raise ValueError(f"Unsupported ranker: {self.hybrid_ranker}")

        res = self.client.hybrid_search(
            self.collection_name,
            [dense_req, sparse_req],
            ranker=ranker,
            limit=query.similarity_top_k,
            output_fields=output_fields,
            partition_names=kwargs.get("milvus_partition_names"),  # Add partition support
        )

        nodes, similarities, ids = self._parse_from_milvus_results(res)
        return nodes, similarities, ids

    def get_nodes(
        self,
        node_ids: list[str] | None = None,
        filters: MetadataFilters | None = None,
        namespaces: list[str] | None = None,
        **kwargs: Any,
    ) -> list[BaseNode]:
        partition_names: list[str] | None = kwargs.get("milvus_partition_names")
        if partition_names is None and namespaces:
            partition_names = self.document_partition_names(namespaces)
            kwargs["milvus_partition_names"] = partition_names
        self._ensure_collection_loaded(partition_names)
        return super().get_nodes(node_ids=node_ids, filters=filters, **kwargs)

    def delete(self, ref_doc_id: str, **delete_kwargs: Any) -> None:
        """LlamaIndex's delete, across the whole collection.

        It does not know the document's namespace, so it loads every partition. Callers that know the namespace use
        ``delete_documents``, which loads only the partitions involved.
        """
        self._ensure_collection_loaded()
        super().delete(ref_doc_id)

    def document_partition_names(self, namespaces: list[str]) -> list[str]:
        """Every partition the nodes of documents in these namespaces can live in.

        ``_default`` is always included: nodes written while a collection was not yet fully partitioned landed
        there (#1923) and stay until repaired, and a read or delete that skips it misses them. A half-built
        collection may lack a hashed partition, which Milvus rejects by name, and nothing can be stored in a
        partition that does not exist. A legacy collection has no manual partitions, so ``_default`` is all it has.
        """
        state = self.partition_state()
        if state is MilvusPartitionState.LEGACY:
            return [DEFAULT_PARTITION_NAME]

        partition_names = list(dict.fromkeys(get_partition_names_for_namespaces(namespaces=namespaces)))
        if state is MilvusPartitionState.PARTIAL:
            existing = self._manual_partition_names()
            partition_names = [name for name in partition_names if name in existing]
        return [*partition_names, DEFAULT_PARTITION_NAME]

    def delete_documents(self, ref_doc_ids: list[str], namespaces: list[str]) -> int:
        """Delete every node of these documents with a filtered delete; returns the number of deleted nodes.

        Only the partitions the namespaces hash to are loaded, never the whole collection, which on a
        partitioned store does not fit in memory. Deleting nothing succeeds, so a retried removal is safe.
        """
        if not ref_doc_ids:
            return 0

        partition_names = self.document_partition_names(namespaces)
        self._ensure_collection_loaded(partition_names)

        deleted = 0
        for batch in iter_batch(ref_doc_ids, DOCUMENT_IDS_PER_DELETE_EXPRESSION):
            doc_ids_expr = ['"' + entry + '"' for entry in batch]
            for partition_name in partition_names:
                result = self.client.delete(
                    collection_name=self.collection_name,
                    filter=f"{self.doc_id_field} in [{','.join(doc_ids_expr)}]",
                    partition_name=partition_name,
                )
                deleted += self._deleted_count(result)
        return deleted

    def node_ids_by_document(self, partition_name: str) -> dict[str, list[str]]:
        """Primary keys of every node in one partition, grouped by document id.

        Milvus has no DISTINCT, so the grouping happens here while paging through the partition.
        """
        self._ensure_collection_loaded([partition_name])
        node_ids: dict[str, list[str]] = {}
        for page in self._partition_pages(partition_name, ["id", self.doc_id_field], f'{self.doc_id_field} != ""'):
            for row in page:
                node_ids.setdefault(row[self.doc_id_field], []).append(row["id"])
        return node_ids

    def _partition_pages(
        self, partition_name: str, output_fields: list[str], filter_expression: str
    ) -> Iterator[list[dict[str, Any]]]:
        """Page through one partition; a plain query is capped at Milvus' result window, an iterator is not."""
        iterator = self.client.query_iterator(
            collection_name=self.collection_name,
            batch_size=NODES_PER_SCAN_PAGE,
            filter=filter_expression,
            output_fields=output_fields,
            partition_names=[partition_name],
        )
        try:
            while page := iterator.next():
                yield page
        finally:
            iterator.close()

    def stranded_nodes(self) -> list[StoredNodeKey]:
        """Nodes in ``_default`` of a partitioned collection, written while it was half-built (#1923).

        A legacy collection has none: ``_default`` is where all of its nodes belong.
        """
        if self.partition_state() is MilvusPartitionState.LEGACY:
            return []
        return self._node_keys(DEFAULT_PARTITION_NAME, f'{self.doc_id_field} != ""')

    def node_keys_of_document(self, document_id: str, namespace: str) -> list[StoredNodeKey]:
        """The document's nodes in its namespace's partition, where readers look for them."""
        return self._node_keys(get_partition_name_for_namespace(namespace), f'{self.doc_id_field} == "{document_id}"')

    def _node_keys(self, partition_name: str, filter_expression: str) -> list[StoredNodeKey]:
        self._ensure_collection_loaded([partition_name])
        return [
            StoredNodeKey.from_row(row)
            for page in self._partition_pages(partition_name, StoredNodeKey.output_fields(), filter_expression)
            for row in page
        ]

    def restore_stranded_nodes(self, node_ids_by_namespace: dict[str, list[str]]) -> int:
        """Copy nodes from ``_default`` into their namespaces' partitions as stored; returns the number copied.

        Nothing is parsed or embedded again. ``*`` leaves out the BM25 output, which Milvus refuses to return and
        recomputes from ``text`` on insert. The flush makes the copies durable before the caller deletes the
        originals. It runs once for every namespace: Milvus allows a collection one flush every 10 s
        (``quotaAndLimits.flushRate``), so a flush per document would stretch a large repair into hours.
        """
        copied = sum(
            self._copy_from_default(node_ids, get_partition_name_for_namespace(namespace))
            for namespace, node_ids in node_ids_by_namespace.items()
            if node_ids
        )
        if copied:
            self.client.flush(self.collection_name)
        return copied

    def _copy_from_default(self, node_ids: list[str], partition_name: str) -> int:
        self._ensure_collection_loaded([DEFAULT_PARTITION_NAME, partition_name])
        copied = 0
        for batch in iter_batch(node_ids, NODE_IDS_PER_DELETE):
            ids_expr = ",".join(f'"{node_id}"' for node_id in batch)
            for page in self._partition_pages(DEFAULT_PARTITION_NAME, ["*"], f"id in [{ids_expr}]"):
                for rows in iter_batch(page, self.batch_size):
                    self.client.upsert(collection_name=self.collection_name, data=rows, partition_name=partition_name)
                copied += len(page)
        return copied

    def delete_stranded_nodes(self, node_ids: list[str]) -> int:
        """Delete nodes from ``_default`` by primary key; returns the number of deleted nodes."""
        return self.delete_nodes_in_partition(node_ids, DEFAULT_PARTITION_NAME)

    def delete_nodes_in_partition(self, node_ids: list[str], partition_name: str) -> int:
        """Delete nodes by primary key; returns the number of deleted nodes."""
        deleted = 0
        for batch in iter_batch(node_ids, NODE_IDS_PER_DELETE):
            result = self.client.delete(collection_name=self.collection_name, ids=batch, partition_name=partition_name)
            deleted += self._deleted_count(result)
        return deleted

    @staticmethod
    def _deleted_count(result: dict[str, int] | list[str]) -> int:
        """pymilvus returns the deleted primary keys when the server reports them, else a ``delete_count``."""
        if isinstance(result, list):
            return len(result)
        return result.get("delete_count", 0)

    def delete_by_namespace(self, namespace: str) -> None:
        """Delete every vector of a namespace via a metadata-filtered delete.

        Namespaces hash into shared partitions (collisions are expected — see milvus_partition_manager),
        so this MUST filter on ``namespace ==`` and MUST NOT drop the partition: a partition drop would
        also wipe the vectors of any other namespace that hashed to the same partition. ``_default`` is
        covered too (see ``document_partition_names``), because all-namespaces retrieval still finds nodes
        stranded there.
        """
        partition_names = (
            [None]
            if self.partition_state() is MilvusPartitionState.LEGACY
            else self.document_partition_names([namespace])
        )
        self._ensure_collection_loaded([name for name in partition_names if name])
        for partition_name in partition_names:
            self.client.delete(
                collection_name=self.collection_name,
                filter=f'{NAMESPACE} == "{namespace}"',
                partition_name=partition_name,
            )

    def drop_collection(self) -> None:
        """Drop the whole collection backing a knowledge database. Idempotent — a missing collection is fine."""
        if self.client.has_collection(collection_name=self.collection_name):
            self.client.drop_collection(collection_name=self.collection_name)

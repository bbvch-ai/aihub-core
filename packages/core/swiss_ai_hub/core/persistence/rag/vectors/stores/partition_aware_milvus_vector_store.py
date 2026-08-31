import json
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
    MAX_PARTITIONS,
    get_partition_name_for_namespace,
    get_partition_names_for_namespaces,
)

try:
    from pymilvus import AnnSearchRequest, RRFRanker, WeightedRanker
except ImportError:
    AnnSearchRequest = None
    RRFRanker = None
    WeightedRanker = None

MILVUS_DYNAMIC_FIELD_MAX_BYTES = 65536


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

    Backward compatibility: Falls back to base class for collections that do not have exactly 1023 manual partitions
    (e.g., collections created before this PR or with a different partition count).
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

        self._has_manual_partitions: bool | None = None
        self._declared_fields: set[str] | None = None

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

    def _check_has_manual_partitions(self) -> bool:
        """Check if collection has 1023 manual partitions (partition_0...partition_1022)."""
        if self._has_manual_partitions is None:
            partitions = self.client.list_partitions(collection_name=self.collection_name)
            manual_partitions = [p for p in partitions if p.startswith("partition_")]
            self._has_manual_partitions = len(manual_partitions) == MAX_PARTITIONS

        return self._has_manual_partitions

    def add(self, nodes: list[BaseNode], **add_kwargs: Any) -> list[str]:
        """
        Insert nodes into their hashed partitions (or fallback to base class if no manual partitions).

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

        if not self._check_has_manual_partitions():
            self._ensure_collection_loaded()
            return super().add(nodes, **add_kwargs)

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

    def _declared_field_names(self) -> set[str]:
        """
        Resolve declared columns from the live collection rather than restating the schema, which lives in
        milvus_vector_store_factory and would drift. The store attributes alone are not enough either —
        namespace is a declared column with no corresponding attribute.
        """
        if self._declared_fields is None:
            description = self.client.describe_collection(collection_name=self.collection_name)
            self._declared_fields = {field["name"] for field in description["fields"]}

        return self._declared_fields

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
        # Backward compatibility: fallback to base class if no manual partitions
        if not self._check_has_manual_partitions():
            self._ensure_collection_loaded()
            return super().query(query, **kwargs)

        namespaces = self._extract_namespaces_from_query(query)
        partition_names: list[str] | None = None
        if namespaces:
            partition_names = get_partition_names_for_namespaces(namespaces=namespaces)
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
            partition_names = get_partition_names_for_namespaces(namespaces=namespaces)
            kwargs.setdefault("milvus_partition_names", partition_names)
        self._ensure_collection_loaded(partition_names)
        return super().get_nodes(node_ids=node_ids, filters=filters, **kwargs)

    def delete(self, ref_doc_id: str, **delete_kwargs: Any) -> None:
        """
        Delete nodes associated with a ref_doc_id, scoped to a specific partition.
        """
        # Backward compatibility: fallback to base class if no manual partitions
        if not self._check_has_manual_partitions():
            self._ensure_collection_loaded()
            return super().delete(ref_doc_id)

        partition_name: str | None = delete_kwargs.get("partition_name")
        self._ensure_collection_loaded([partition_name] if partition_name else None)
        doc_ids = [ref_doc_id] if not isinstance(ref_doc_id, list) else ref_doc_id
        doc_ids_expr = ['"' + entry + '"' for entry in doc_ids]

        entries = self.client.query(
            collection_name=self.collection_name,
            filter=f"{self.doc_id_field} in [{','.join(doc_ids_expr)}]",
            partition_names=[partition_name] if partition_name else None,
            output_fields=["id"],
        )

        if len(entries) > 0:
            ids_to_delete = [entry["id"] for entry in entries]

            self.client.delete(
                collection_name=self.collection_name,
                pks=ids_to_delete,
                partition_name=partition_name,
            )

    def delete_by_namespace(self, namespace: str) -> None:
        """Delete every vector of a namespace via a metadata-filtered delete.

        Namespaces hash into shared partitions (collisions are expected — see milvus_partition_manager),
        so this MUST filter on ``namespace ==`` and MUST NOT drop the partition: a partition drop would
        also wipe the vectors of any other namespace that hashed to the same partition.
        """
        partition_name = get_partition_name_for_namespace(namespace) if self._check_has_manual_partitions() else None
        self._ensure_collection_loaded([partition_name] if partition_name else None)
        self.client.delete(
            collection_name=self.collection_name,
            filter=f'{NAMESPACE} == "{namespace}"',
            partition_name=partition_name,
        )

    def drop_collection(self) -> None:
        """Drop the whole collection backing a knowledge database. Idempotent — a missing collection is fine."""
        if self.client.has_collection(collection_name=self.collection_name):
            self.client.drop_collection(collection_name=self.collection_name)

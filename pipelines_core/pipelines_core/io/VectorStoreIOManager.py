from typing import List, Sequence, Union

from dagster import (
    ConfigurableIOManager,
    InputContext,
    OutputContext,
    ResourceDependency,
)
from lib_core.constants.node_metadata import DOCUMENT_ID
from llama_index.core.schema import TextNode
from llama_index.core.vector_stores.types import (
    BasePydanticVectorStore,
    MetadataFilter,
    MetadataFilters,
)
from llama_index.vector_stores.milvus import MilvusVectorStore

from pipelines_core.util.id_utils import uri_to_id


class VectorStoreIOManager(ConfigurableIOManager):
    """
    VectorStoreIOManager for loading and storing TextNodes from/to the vector store.

    This IO Manager handles reading and writing to a vector store. Wrap any asset with this IO manager
    and its output will be stored in the vector store, while the input of any consecutive asset will
    be loaded from the vector store.

    The VectorStoreIOManager depends on the ``"vector_store"`` resource, which should be a
    ``*VectorStore*`` instance from ``"llama_index"``.

    This IO Manager assumes partitioning. The partition key must either be a document ID or a document URI.
    Document URIs usually originate from the data lake and can be converted to document IDs using the
    ``"uri_to_id"`` function from ``"pipelines.util.id_utils"``, as a document ID is just a hash of the
    document URI.

    The VectorStoreIOManager can handle the following cases:
    - **Partitioned asset**: The IO Manager wraps an asset that is partitioned. In this case, the IO Manager
      will load the TextNodes corresponding to the partition key (either ID or URI).
    - **Non-partitioned asset**: The IO Manager wraps an asset that is not partitioned. In this case, the IO Manager
      assumes that the upstream asset was partitioned and will load all TextNodes corresponding to all
      partition keys available to the upstream dependency. The output will be a list of lists of TextNodes,
      where each sublist corresponds to a document.

    **Note**: The IO Manager currently does not handle the case in which the pipeline is not partitioned
    and only handles a single Document.

    Example usage:

    1. Attach an IO manager to a set of assets using the resource key ``"vector_store_io_manager"``

    .. code-block:: python

        from pipelines_core.io.VectorStoreIOManager import VectorStoreIOManager
        from pipelines_core.resources.vector_store.AzureAISearchVectorStoreResource import AzureAISearchVectorStoreResource
        from pipelines_core.resources.organization.NamespaceResource import NamespaceResource

        from dagster import Definitions, asset

        @asset(partitions_def=my_partition, io_manager_key="vector_store_io_manager")
        def text_nodes(ref_doc: RefDocDocument) -> List[TextNode]:
            # TextNodes returned by this asset will be stored in the vector store
            ...

        @asset(partitions_def=my_partition)
        def downstream_asset(text_nodes: List[TextNode]):
            # TextNodes loaded from the vector store
            ...

        namespace = NamespaceResource(name="my_namespace", organization="my_organization")
        vector_store = AzureAISearchVectorStoreResource(namespace=namespace)
        vector_store_io_manager = VectorStoreIOManager(vector_store=vector_store)

        defs = Definitions(
            assets=[text_nodes, downstream_asset],
            resources={
                "namespace": namespace,
                "vector_store": vector_store,
                "vector_store_io_manager": vector_store_io_manager,
            },
        )

    """

    vector_store: ResourceDependency[BasePydanticVectorStore]
    document_id_key: str = DOCUMENT_ID

    def handle_output(
        self, context: OutputContext, obj: Union[List[TextNode], List[List[TextNode]]]
    ) -> None:
        # Check if obj is a list of TextNodes (single document)
        if isinstance(obj, list) and all(isinstance(node, TextNode) for node in obj):
            nodes = obj
            context.log.info(
                f"Adding {len(nodes)} nodes from a single document to vector store"
            )
        # Check if obj is a list of lists of TextNodes (multiple documents)
        elif isinstance(obj, list) and all(
            isinstance(sublist, list)
            and all(isinstance(node, TextNode) for node in sublist)
            for sublist in obj
        ):
            # Flatten the list of lists
            nodes = [node for sublist in obj for node in sublist]
            context.log.info(
                f"Adding {len(nodes)} nodes from multiple documents to vector store"
            )
        else:
            context.log.error("Output must be a List[TextNode] or List[List[TextNode]]")
            raise ValueError("Expected a List[TextNode] or List[List[TextNode]]")

        if not nodes:
            context.log.warning("No nodes to add to vector store")
            return

        # In milvus, IDs are not unique. Adding nodes with the same ID will NOT overwrite the existing node
        # but rather create a duplicate. To avoid this, we first delete the existing nodes with the same ID
        # Meanwhile, Azure does not support filtering for document IDs, hence we need to treat these two
        # vector stores differently. Sucks, but that's how it is.
        if isinstance(self.vector_store, MilvusVectorStore):
            self.vector_store.delete_nodes([node.id_ for node in nodes])

        self.vector_store.add(nodes)
        context.log.info("Successfully added nodes to vector store")

    def load_input(
        self, context: InputContext
    ) -> Union[List[TextNode], List[List[TextNode]]]:
        # Check if a partition key is available
        if context.has_partition_key:
            # Single partition key; load nodes for a single document
            doc_id = self._convert_partition_key_to_doc_id(
                context.partition_key, context
            )
            nodes = self._query_vector_store_for_single_doc(doc_id, context)
            return nodes  # Return List[TextNode]
        else:
            # No partition key; load nodes for all partition keys from the upstream asset
            upstream_output = context.upstream_output
            partitions_def = upstream_output.asset_partitions_def

            if partitions_def is not None:
                # Get all partition keys from the upstream asset
                all_partition_keys = partitions_def.get_partition_keys(
                    dynamic_partitions_store=context.instance
                )
                doc_ids = self._get_doc_ids_from_partition_keys(
                    all_partition_keys, context
                )
                nodes_per_doc = self._query_vector_store_for_multiple_docs(
                    doc_ids, context
                )
                return nodes_per_doc  # Return List[List[TextNode]]
            else:
                context.log.error(
                    "No partition definition found for the upstream asset."
                )
                raise ValueError("Cannot load nodes without partition information.")

    def _convert_partition_key_to_doc_id(
        self, uri_or_id: str, context: InputContext
    ) -> str:
        if "/" in uri_or_id:
            doc_id = uri_to_id(uri_or_id)
            context.log.debug(f"Converted URI {uri_or_id} to ID {doc_id}")
        else:
            doc_id = uri_or_id
        return doc_id

    def _get_doc_ids_from_partition_keys(
        self, partition_keys: Sequence[str], context: InputContext
    ) -> List[str]:
        doc_ids = []
        for uri_or_id in partition_keys:
            doc_id = self._convert_partition_key_to_doc_id(uri_or_id, context)
            doc_ids.append(doc_id)
        return doc_ids

    def _query_vector_store_for_single_doc(
        self, doc_id: str, context: InputContext
    ) -> List[TextNode]:
        filters = MetadataFilters(
            filters=[MetadataFilter(key=self.document_id_key, value=doc_id)]
        )

        context.log.info(f"Querying vector store for document ID: {doc_id}")

        nodes = self.vector_store.get_nodes(filters=filters)

        context.log.info(f"Found {len(nodes)} nodes for document {doc_id}")

        if not nodes:
            context.log.warning(f"No nodes found for document {doc_id}")

        return nodes

    def _query_vector_store_for_multiple_docs(
        self, doc_ids: List[str], context: InputContext
    ) -> List[List[TextNode]]:
        nodes_per_doc = []
        for doc_id in doc_ids:
            nodes = self._query_vector_store_for_single_doc(doc_id, context)
            nodes_per_doc.append(nodes)

        return nodes_per_doc

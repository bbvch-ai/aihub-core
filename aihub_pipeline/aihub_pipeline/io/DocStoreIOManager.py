from dagster import ConfigurableIOManager, InputContext, OutputContext, ResourceDependency
from llama_index.core.storage.docstore.keyval_docstore import KVDocumentStore

from aihub_pipeline.types.RefDocDocument import RefDocDocument
from aihub_pipeline.util.id_utils import uri_to_id


class DocStoreIOManager(ConfigurableIOManager):
    """DocStoreIOManager for loading and storing RefDocs from/to the document store.

    This IO Manager handles reading and writing to a document store. Wrap any asset with this IO manager
    and its output will be stored in the document store, while the input of any consecutive asset will
    be loaded from the document store.

    The DocStoreIOManager depends on the ``"doc_store"`` resource, which should be a ``*KVDocumentStore*``
    from ``"llama_index"``.

    This IO Manager assumes partitioning. The Partition key must either be a document ID or a document URI.
    Document URIs usually originate from the data lake and can be converted to document IDs using the
    ``"uri_to_id"`` function from ``"pipelines.util.id_utils"``, as a document ID is just a hash of the
    document URI.
    The DocStoreIOManager can handle the following case:
    - **partitioned asset**: The IO Manager wraps an asset that is partitioned. In this case, the IO Manager
    will load the RefDoc file corresponding to the partition key (either ID or URI).
    - **non-partitioned asset**: The IO Manager wraps an asset that is not partitioned. In this case, the IO Manager
    assumes that the upstream asset was partitioned and will load all ref docs corresponding to all
    partition keys available to the upstream dependency.

    **Note**: The IO Manager currently does not handle the case in which the pipeline is not partitioned
    and only handles a single ref doc.

    Example usage:

    1. Attach an IO manager to a set of assets using the resource key ``"doc_store_io_manager"``

    .. code-block:: python

        from aihub_pipeline.io.DocStoreIOManager import DocStoreIOManager
        from aihub_pipeline.resources.doc_store.MongoDocumentStoreResource import MongoDocumentStoreResource

        from dagster import Definitions, asset

        @asset(partitions_def=my_partition,io_manager_key="doc_store_io_manager")
        def ref_doc(data_lake_file: DataLakeFile) -> RefDocDocument:
            # RefDocDocument returned by this asset will be stored in the document store
            return RefDocDocument(text="").add_metadata_from_data_lake_file(data_lake_file)

        @asset(partitions_def=my_partition)
        def downstream_asset(ref_doc: RefDocDocument):
            # RefDocDocument loaded from the document store
            ...

        doc_store = MongoDocumentStoreResource(document_store_name="my_doc_store")
        doc_store_io_manager = DocStoreIOManager(doc_store=doc_store)

        defs = Definitions(
            assets=[ref_doc, downstream_asset],
            resources={
                "doc_store": doc_store,
                "doc_store_io_manager": doc_store_io_manager,
            },
        )
    """

    doc_store: ResourceDependency[KVDocumentStore]

    def handle_output(self, context: OutputContext, obj: RefDocDocument | list[RefDocDocument]) -> None:
        if isinstance(obj, RefDocDocument):
            documents = [obj]
        elif isinstance(obj, list):
            documents = obj
        else:
            context.log.error("Output is neither a RefDocDocument nor a list of RefDocDocuments.")
            raise ValueError("Expected a RefDocDocument or a list of RefDocDocuments.")

        for document in documents:
            context.log.info(f"Adding document to docstore: {document.id_}")

        self.doc_store.add_documents(documents)

    def get_ref_doc(self, uri_or_id: str, context: InputContext):
        doc_id = self._convert_partition_key_to_doc_id(uri_or_id, context)
        context.log.info(f"Loading document with ID: {doc_id}")
        document = self.doc_store.get_document(doc_id)
        return RefDocDocument(**document.to_dict())

    def load_input(self, context: InputContext) -> RefDocDocument | list[RefDocDocument]:
        # Check if a partition key is available
        if context.has_partition_key:
            # If partition key is present, use it to load the document
            return self.get_ref_doc(context.partition_key, context)

        else:
            # No partition key, load all documents for all partition keys
            upstream_output = context.upstream_output
            partitions_def = upstream_output.asset_partitions_def

            if partitions_def is not None:
                # Get all partition keys from the upstream asset
                all_partition_keys = partitions_def.get_partition_keys(dynamic_partitions_store=context.instance)
                ref_docs = []
                for partition_key in all_partition_keys:
                    ref_doc = self.get_ref_doc(partition_key, context)
                    ref_docs.append(ref_doc)
                return ref_docs  # Return the list of loaded documents
            else:
                context.log.error("No partition definition found for the upstream asset.")
                raise ValueError("Cannot load documents without partition information.")

    def _convert_partition_key_to_doc_id(self, uri_or_id: str, context: InputContext):
        if "/" in uri_or_id:
            doc_id = uri_to_id(uri_or_id)
            context.log.debug(f"Converted URI {uri_or_id} to ID {doc_id}")
        else:
            doc_id = uri_or_id
        return doc_id

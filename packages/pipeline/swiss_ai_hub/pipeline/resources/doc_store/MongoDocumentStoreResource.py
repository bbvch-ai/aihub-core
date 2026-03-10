from dagster import ConfigurableResource, InitResourceContext
from llama_index.storage.docstore.mongodb import MongoDocumentStore
from swiss_ai_hub.core.persistence.rag.documents.stores.docstore import create_mongo_document_store


class MongoDocumentStoreResource(ConfigurableResource[MongoDocumentStore]):
    """
    This resource represents a MongoDocumentStore with an active connection.

    Use this resource either stand-alone whenever you want to directly interact with the document store,
    or use it in conjunction with the ``"doc_store_io_manager"`` resource for a more integrated experience.

    Example usage:

    1. Use the Document store as a stand-alone resource

    ... code-block:: python

        from swiss_ai_hub.pipeline.resources.doc_store.MongoDocumentStoreResource import MongoDocumentStoreResource

        from dagster import Definitions, asset

        @asset
        def asset1(doc_store: MongoDocumentStore):
            doc_store.get_document("my_doc_id")


        defs = Definitions(
            assets=[asset1],
            resources={
                "doc_store": MongoDocumentStoreResource(
                    document_store_name="my_document_store"
                ),
            }
        )
    ...

    2. Use the Document store in conjunction with a doc store IO Manager ``"doc_store_io_manager"``

    ... code-block:: python

        from swiss_ai_hub.pipeline.io.DocStoreIOManager import DocStoreIOManager
        from swiss_ai_hub.pipeline.resources.doc_store.MongoDocumentStoreResource import MongoDocumentStoreResource

        from dagster import Definitions, asset

        @asset(partitions_def=my_partition,io_manager_key="doc_store_io_manager")
        def ref_doc(data_lake_file: DataLakeFile) -> RefDocDocument:
            # RefDocDocument returned by this asset will be stored in the document store
            return RefDocDocument(text="").add_metadata_from_data_lake_file(data_lake_file)

        @asset(partitions_def=my_partition)
        def downstream_asset(ref_doc: RefDocDocument):
            # RefDocDocument loaded from the document store
            ...

        doc_store = MongoDocumentStoreResource(document_store_name="my_document_store")
        doc_store_io_manager = DocStoreIOManager(doc_store=doc_store)

        defs = Definitions(
            assets=[ref_doc, downstream_asset],
            resources={
                "doc_store": doc_store,
                "doc_store_io_manager": doc_store_io_manager,
            }
        )
    ...
    """

    document_store_name: str

    def create_resource(self, context: InitResourceContext) -> MongoDocumentStore:
        return create_mongo_document_store(self.document_store_name)

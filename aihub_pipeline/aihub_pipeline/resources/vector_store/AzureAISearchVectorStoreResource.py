from dagster import ConfigurableResource, InitResourceContext
from llama_index.vector_stores.azureaisearch import AzureAISearchVectorStore

from aihub_lib.persistence.rag.vectors.stores.AzureAISearchVectorStoreFactory import (
    create_azure_ai_search_vector_store,
)


class AzureAISearchVectorStoreResource(ConfigurableResource):
    """
    This resource represents a AzureAISearchVectorStore.

    Use this resource either stand-alone whenever you must directly interact with the vector store,
    or use it in conjunction with the ``"vector_store_io_manager"`` resource for a more integrated experience.

    Example usage:

    1. Use the Vector Store as a stand-alone resource

    .. code-block:: python

        from aihub_pipeline.resources.vector_store.AzureAISearchVectorStoreResource import AzureAISearchVectorStoreResource

        from dagster import Definitions, asset

        @asset
        def asset1(vector_store: AzureAISearchVectorStoreResource):
            nodes = vector_store.query(...")


        defs = Definitions(
            assets=[asset1],
            resources={
                "vector_store": AzureAISearchVectorStoreResource(
                    vector_store_name="my_vector_store"
                ),
            },
        )

    2. Use the Vector store in conjunction with a vector store IO Manager ``"vector_store_io_manager"``

    ... code-block:: python

        from aihub_pipeline.io.VectorStoreIOManager import VectorStoreIOManager
        from aihub_pipeline.resources.vector_store.AzureAISearchVectorStoreResource import AzureAISearchVectorStoreResource

        from dagster import Definitions, asset

        @asset(partitions_def=my_partition, io_manager_key="vector_store_io_manager")
        def text_nodes(ref_doc: RefDocDocument) -> List[TextNode]:
            # TextNodes returned by this asset will be stored in the vector store
            ...

        @asset(partitions_def=my_partition)
        def downstream_asset(text_nodes: List[TextNode]):
            # TextNodes loaded from the vector store
            ...

        vector_store = AzureAISearchVectorStoreResource(vector_store_name="my_vector_store")
        vector_store_io_manager = VectorStoreIOManager(vector_store=vector_store)

        defs = Definitions(
            assets=[text_nodes, downstream_asset],
            resources={
                "vector_store": vector_store,
                "vector_store_io_manager": vector_store_io_manager,
            },
        )

    """

    vector_store_name: str

    def create_resource(self, context: InitResourceContext) -> AzureAISearchVectorStore:
        return create_azure_ai_search_vector_store(self.vector_store_name)

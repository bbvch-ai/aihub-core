from dagster import ConfigurableResource, InitResourceContext, ResourceDependency
from llama_index.vector_stores.azureaisearch import AzureAISearchVectorStore

from lib_core.stores.AzureAISearchVectorStoreFactory import create_azure_ai_search_vector_store
from pipelines_core.resources.organization.NamespaceResource import NamespaceResource


class AzureAISearchVectorStoreResource(ConfigurableResource):
    """
    This resource represents a AzureAISearchVectorStore.

    Use this resource either stand-alone whenever you must directly interact with the vector store,
    or use it in conjunction with the ``"vector_store_io_manager"`` resource for a more integrated experience.

    Example usage:

    1. Use the Vector Store as a stand-alone resource

    .. code-block:: python

        from pipelines_core.resources.vector_store.AzureAISearchVectorStoreResource import AzureAISearchVectorStoreResource
        from pipelines_core.resources.organization.NamespaceResource import NamespaceResource

        from dagster import Definitions, asset

        @asset
        def asset1(vector_store: AzureAISearchVectorStoreResource):
            nodes = vector_store.query(...")


        defs = Definitions(
            assets=[asset1],
            resources={
                "vector_store": AzureAISearchVectorStoreResource(
                    namespace=NamespaceResource(name="my_namespace", organization="my_organization"),
                ),
            },
        )

    2. Use the Vector store in conjunction with a vector store IO Manager ``"vector_store_io_manager"``

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

    namespace: ResourceDependency[NamespaceResource]

    def create_resource(self, context: InitResourceContext) -> AzureAISearchVectorStore:
        return create_azure_ai_search_vector_store(self.namespace.organization)

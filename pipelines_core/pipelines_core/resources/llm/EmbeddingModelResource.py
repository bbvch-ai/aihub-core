from dagster import ConfigurableResource, ResourceDependency, InitResourceContext
from llama_index.core.base.embeddings.base import BaseEmbedding

from pipelines_core.pipelines_core.resources.llm.LlmHandlerResource import LlmHandlerResource


class EmbeddingModelResource(ConfigurableResource[BaseEmbedding]):
    """
    This resource provides an embedding model for the use in any operation or asset.
    As most pipelines need the same embedding model throughout all steps, it is simpler
    to just provide this global embedding model as a resource than each pipeline step having
    to access the LLM Handler and pick a model to their liking.

    To configure this resource, provide the llm handler as well as the model name.

    Example usage:

    1. Use the embedding model in an asset:

    .. code-block:: python

        from pipelines_core.resources.llm.EmbeddingModelResource import EmbeddingModelResource
        from pipelines_core.resources.llm.LlmHandlerResource import LlmHandlerResource
        from pipelines_core.resources.organization.NamespaceResource import NamespaceResource

        from dagster import Definitions, asset

        @asset
        def asset1(embedding_model: ResourceParam[BaseEmbedding]):
            embeddings = embedding_model.get_text_embedding("test")

        namespace = NamespaceResource(name="my_namespace", organization="my_organization")
        llm_handler_resource = LlmHandlerResource(namespace=namespace)

        defs = Definitions(
            assets=[asset1],
            resources={
                "embedding_model": EmbeddingModelResource(
                        llm_handler_resource=llm_handler_resource,
                        model_name="text-embedding-ada-002",
                    )
                }
        )

    """

    llm_handler_resource: ResourceDependency[LlmHandlerResource]
    model_name: str

    def create_resource(self, context: InitResourceContext) -> BaseEmbedding:
        model = self.llm_handler_resource.embedding_model(
            name=self.model_name,
        )
        if not isinstance(model, BaseEmbedding):
            raise ValueError(f"Model {self.model_name} is not an embedding model.")

        return model

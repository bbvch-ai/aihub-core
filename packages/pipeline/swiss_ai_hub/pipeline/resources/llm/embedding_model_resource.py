from dagster import ConfigurableResource, InitResourceContext, ResourceDependency
from llama_index.core.base.embeddings.base import BaseEmbedding
from swiss_ai_hub.core.generative_ai.resources.models.llm.embedding_model_config import EmbeddingModelConfig


class EmbeddingModelResource(ConfigurableResource[BaseEmbedding]):
    """
    This resource provides an embedding model for the use in any operation or asset.
    As most pipelines need the same embedding model throughout all steps, it is simpler
    to just provide this global embedding model as a resource than each pipeline step having
    to pick a model to their liking.

    Example usage:

    1. Use the embedding model in an asset:

    ... code-block:: python

        from swiss_ai_hub.pipeline.resources.llm.embedding_model_resource import EmbeddingModelResource

        from dagster import Definitions, asset

        @asset
        def asset1(embedding_model: ResourceParam[BaseEmbedding]):
            embeddings = embedding_model.get_text_embedding("test")

        defs = Definitions(
            assets=[asset1],
            resources={
                "embedding_model": EmbeddingModelResource(
                    embedding_config=AzureOpenAIEmbeddingConfig(
                        name="text-embedding-ada-002",
                        base_url="https://aihub-dev-openai-che.openai.azure.com/",
                        api_version="2024-12-01-preview",
                        embedding_tokens_costs_per_thousand=0.0,
                        default_parameter=EmbeddingModelConfig(model_name="azure/text-embedding-3-large"),
                    )
                )
            }
        )

    """

    embedding_config: ResourceDependency[EmbeddingModelConfig]

    def create_resource(self, context: InitResourceContext) -> BaseEmbedding:
        model, _ = self.embedding_config.to_llama_index()
        if not isinstance(model, BaseEmbedding):
            raise ValueError("The returned model is not an instance of BaseEmbedding.")
        return model

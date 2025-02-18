from dagster import ConfigurableResource, InitResourceContext
from llama_index.core.base.embeddings.base import BaseEmbedding

from aihub_lib.generative_ai.resources.models.llm.embedding.azure.AzureOpenAIEmbeddingConfig import (
    AzureOpenAIEmbeddingConfig,
)
from aihub_lib.generative_ai.resources.models.llm.embedding.self_hosted.SelfHostedEmbeddingConfig import (
    SelfHostedEmbeddingConfig,
)


class EmbeddingModelResource(ConfigurableResource[BaseEmbedding]):
    """
    This resource provides an embedding model for the use in any operation or asset.
    As most pipelines need the same embedding model throughout all steps, it is simpler
    to just provide this global embedding model as a resource than each pipeline step having
    to pick a model to their liking.

    Example usage:

    1. Use the embedding model in an asset:

    ... code-block:: python

        from aihub_pipeline.resources.llm.EmbeddingModelResource import EmbeddingModelResource

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
                        api_version="2023-12-01-preview",
                        embedding_tokens_costs_per_thousand=0.0,
                        default_parameter=AzureOpenAIEmbeddingParameter(),
                    )
                )
            }
        )

    """

    embedding_config: SelfHostedEmbeddingConfig | AzureOpenAIEmbeddingConfig

    def create_resource(self, context: InitResourceContext) -> BaseEmbedding:
        model, _ = self.embedding_config.to_llama_index(self.embedding_config.default_parameter)
        return model

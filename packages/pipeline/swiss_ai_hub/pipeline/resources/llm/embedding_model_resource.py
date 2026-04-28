from dagster import ConfigurableResource, InitResourceContext, ResourceDependency
from llama_index.core.base.embeddings.base import BaseEmbedding
from swiss_ai_hub.core.generative_ai.resources.models.llm.embedding_model_config import EmbeddingModelConfig

from swiss_ai_hub.pipeline.resources.llm.litellm_headers import PIPELINE_REDACTION_HEADERS


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
                    embedding_config=EmbeddingModelConfig(model_name="embedding/bge-m3"),
                )
            }
        )

    """

    embedding_config: ResourceDependency[EmbeddingModelConfig]

    def create_resource(self, context: InitResourceContext) -> BaseEmbedding:
        model, _ = self.embedding_config.to_llama_index(extra_headers=PIPELINE_REDACTION_HEADERS)
        if not isinstance(model, BaseEmbedding):
            raise ValueError("The returned model is not an instance of BaseEmbedding.")
        return model

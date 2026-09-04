import logging
from functools import cache
from typing import Annotated

from mongoengine import DoesNotExist
from swiss_ai_hub.core.generative_ai.resources.models.llm.embedding_model_config import EmbeddingModelConfig
from swiss_ai_hub.core.generative_ai.resources.models.llm.llm_config import LLMConfig
from swiss_ai_hub.core.infrastructure import DocumentIngestionPipelineSettings
from swiss_ai_hub.core.persistence import BucketEntity

from swiss_ai_hub.pipeline.resources.llm.litellm_headers import PIPELINE_REDACTION_HEADERS
from swiss_ai_hub.pipeline.util.bucket_utils import ensure_main_db_connection

logger = logging.getLogger(__name__)

"""Per-bucket model resolution for the Generic Document Ingestion Pipeline.

A pipeline serves many knowledge databases and each may be ingested with different models, so the model
cannot be baked into a resource at ``Definitions``-build time any more than a store can. The bucket is
resolved from the run (see ``run_routing``) and the model configuration is built here.

A database created before models were configurable stores none, and falls back to the deployment's own
defaults — so it keeps ingesting with exactly what it used before.
"""


def _bucket_entity(bucket: Annotated[str, "Data lake bucket of the knowledge database"]) -> BucketEntity | None:
    ensure_main_db_connection()
    try:
        return BucketEntity.get_bucket_by_bucket_name(bucket)
    except DoesNotExist:
        logger.warning(f"No bucket row for '{bucket}'; falling back to the deployment's default models.")
        return None


def llm_model_name_for_bucket(bucket: str) -> str:
    """Text-generation model this database's summaries, table refinement and figure descriptions use."""
    entity = _bucket_entity(bucket)
    return (entity.llm_model if entity else None) or DocumentIngestionPipelineSettings().LLM_MODEL


def embedding_model_name_for_bucket(bucket: str) -> str:
    """Embedding model this database is indexed with. Immutable for the database's lifetime."""
    entity = _bucket_entity(bucket)
    return (entity.embedding_model if entity else None) or DocumentIngestionPipelineSettings().EMBEDDING_MODEL


def llm_config_for_bucket(bucket: str) -> LLMConfig:
    return LLMConfig(model_name=llm_model_name_for_bucket(bucket))


def embedding_config_for_bucket(bucket: str) -> EmbeddingModelConfig:
    return EmbeddingModelConfig(model_name=embedding_model_name_for_bucket(bucket))


def embedding_dimension_for_bucket(bucket: str) -> int:
    """Vector width of this database's collection, taken from the model that produces the vectors.

    Derived rather than configured: a dimension set independently of the embedding model is not rejected
    by Milvus, it silently truncates or pads every vector. The API refuses an embedding model that
    declares no ``output_vector_size`` for exactly this reason.
    """
    config = embedding_config_for_bucket(bucket)
    output_vector_size = config.get_model_info()["model_info"].get("output_vector_size")
    if not output_vector_size:
        msg = (
            f"Embedding model '{config.model_name}' declares no output_vector_size, so the vector "
            f"dimension for bucket '{bucket}' cannot be derived. Add it to the LiteLLM model config."
        )
        raise ValueError(msg)
    return int(output_vector_size)


@cache
def build_embedding_model(bucket: str):
    """Embedding model instance for a database, cached so a partition-per-document graph reuses one client."""
    model, _ = embedding_config_for_bucket(bucket).to_llama_index(extra_headers=PIPELINE_REDACTION_HEADERS)
    return model


@cache
def build_language_model(bucket: str):
    """Text-generation model instance for a database, cached per bucket."""
    model, _ = llm_config_for_bucket(bucket).to_llama_index(extra_headers=PIPELINE_REDACTION_HEADERS)
    return model

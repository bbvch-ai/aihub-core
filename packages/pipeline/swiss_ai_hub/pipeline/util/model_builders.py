import logging
from functools import cache
from typing import Annotated

from mongoengine import DoesNotExist
from swiss_ai_hub.core.generative_ai.resources.models.llm.embedding_model_config import EmbeddingModelConfig
from swiss_ai_hub.core.generative_ai.resources.models.llm.llm_config import LLMConfig
from swiss_ai_hub.core.i18n import LocaleString
from swiss_ai_hub.core.infrastructure import DocumentIngestionPipelineSettings
from swiss_ai_hub.core.persistence import BucketEntity

from swiss_ai_hub.pipeline.ingestors.document_ingestion_config import DocumentIngestionConfig
from swiss_ai_hub.pipeline.resources.llm.litellm_headers import PIPELINE_REDACTION_HEADERS
from swiss_ai_hub.pipeline.util.bucket_utils import ensure_main_db_connection

logger = logging.getLogger(__name__)

"""Per-bucket configuration resolution for the Generic Document Ingestion Pipeline.

A pipeline serves many knowledge databases and each carries its own configuration, so nothing about how a
document is processed can be baked into a resource at ``Definitions``-build time any more than a store can. The
bucket is resolved from the run (see ``run_routing``) and its stored configuration is merged over the deployment
defaults here — one place to look for every per-run setting.

A database created before a knob existed stores no value for it and falls back to the deployment's own default,
so it keeps ingesting with exactly what it used before.
"""


def _bucket_entity(bucket: Annotated[str, "Data lake bucket of the knowledge database"]) -> BucketEntity | None:
    ensure_main_db_connection()
    try:
        return BucketEntity.get_bucket_by_bucket_name(bucket)
    except DoesNotExist:
        logger.warning(f"No bucket row for '{bucket}'; falling back to the deployment's default configuration.")
        return None


def _deployment_defaults() -> dict:
    settings = DocumentIngestionPipelineSettings()
    return {
        "llm_model": settings.LLM_MODEL,
        "embedding_model": settings.EMBEDDING_MODEL,
        "vision_model": settings.VISION_MODEL,
        "with_summary_nodes": settings.WITH_SUMMARY_NODES,
        "with_table_refinement": settings.WITH_TABLE_REFINEMENT,
        "with_figure_descriptions": settings.WITH_FIGURE_DESCRIPTIONS,
    }


def ingestor_config_for_bucket[TConfig: DocumentIngestionConfig](
    bucket: str, config_type: type[TConfig] = DocumentIngestionConfig
) -> TConfig:
    """This database's effective configuration: what its row stores, over the deployment defaults.

    A custom pipeline that extended ``DocumentIngestionConfig`` passes its own class to read its extra knobs typed.
    """
    entity = _bucket_entity(bucket)
    stored = {key: value for key, value in (entity.configuration if entity else {}).items() if value is not None}
    identity = {
        "name": entity.name.to_locale_string() if entity else LocaleString(en=bucket),
        "description": entity.description.to_locale_string() if entity else LocaleString(),
    }
    return config_type.model_validate({**identity, **_deployment_defaults(), **stored})


def llm_model_name_for_bucket(bucket: str) -> str:
    """Text-generation model this database's summaries and table refinement use."""
    return ingestor_config_for_bucket(bucket).llm_model


def embedding_model_name_for_bucket(bucket: str) -> str:
    """Embedding model this database is indexed with. Immutable for the database's lifetime."""
    return ingestor_config_for_bucket(bucket).embedding_model


def vision_model_name_for_bucket(bucket: str) -> str:
    """Model that describes this database's figures; the text model unless a vision model was chosen."""
    config = ingestor_config_for_bucket(bucket)
    return config.vision_model or config.llm_model


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


@cache
def build_vision_model(bucket: str):
    """Figure-description model instance for a database, cached per bucket."""
    model, _ = LLMConfig(model_name=vision_model_name_for_bucket(bucket)).to_llama_index(
        extra_headers=PIPELINE_REDACTION_HEADERS
    )
    return model

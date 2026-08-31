from typing import Annotated

from pydantic import Field

from swiss_ai_hub.core.settings.environment_settings import EnvironmentSettings


class DocumentIngestionPipelineSettings(EnvironmentSettings):
    """Deployment-level configuration of the Generic Document Ingestion Pipeline's processing recipe.

    The models are named per deployment: a stack without these exact LiteLLM model names would fail
    every ingest run, and editing the app module is not a deployment knob.
    """

    model_config = EnvironmentSettings.create_settings_config("DOCUMENT_INGESTION_")

    EMBEDDING_MODEL: Annotated[
        str, Field(default="embedding/bge-m3", description="LiteLLM model name used to embed chunks.")
    ]
    LLM_MODEL: Annotated[
        str,
        Field(
            default="text-generation/gemma-4-31B-it",
            description="LiteLLM model name used for summaries, table refinement and figure descriptions.",
        ),
    ]
    WITH_SUMMARY_NODES: Annotated[
        bool, Field(default=True, description="Generate recursive summaries for hierarchical RAG.")
    ]
    WITH_TABLE_REFINEMENT: Annotated[
        bool, Field(default=True, description="Refine tables with the LLM to detect structure and split them.")
    ]
    WITH_FIGURE_DESCRIPTIONS: Annotated[
        bool, Field(default=True, description="Generate figure descriptions with a vision LLM.")
    ]
    OBSERVE_JOB_HOUR: Annotated[
        int, Field(default=0, ge=0, le=23, description="Hour of the daily per-bucket observation schedule.")
    ]
    OBSERVE_JOB_MINUTE: Annotated[
        int, Field(default=0, ge=0, le=59, description="Minute of the daily per-bucket observation schedule.")
    ]

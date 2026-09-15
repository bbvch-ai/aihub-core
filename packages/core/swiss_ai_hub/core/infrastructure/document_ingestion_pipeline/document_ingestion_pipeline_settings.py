from typing import Annotated

from pydantic import Field, field_validator

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
    VISION_MODEL: Annotated[
        str | None,
        Field(
            default=None,
            description="LiteLLM model name used for figure descriptions; the text model when unset.",
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

    @field_validator("VISION_MODEL", mode="before")
    @classmethod
    def _blank_means_unset(cls, value: str | None) -> str | None:
        """Compose substitutes an unset variable with an empty string, which must read as "no vision model"."""
        return value or None

    OBSERVE_JOB_HOUR: Annotated[
        int, Field(default=0, ge=0, le=23, description="Hour of the daily per-bucket observation schedule.")
    ]
    OBSERVE_JOB_MINUTE: Annotated[
        int, Field(default=0, ge=0, le=59, description="Minute of the daily per-bucket observation schedule.")
    ]

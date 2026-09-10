from typing import Annotated

from pydantic import Field

from swiss_ai_hub.core.settings.environment_settings import EnvironmentSettings


class RagImageInlineSettings(EnvironmentSettings):
    """Toggle for inlining RAG figures as base64 at the LiteLLM gateway.

    When enabled the agent signs the figure URL against the internal endpoint so the
    gateway hook can fetch and inline it; when disabled it signs the public URL for the
    provider to fetch directly (pre-inlining behaviour). The gateway hook reads the same
    `RAG_IMAGE_INLINE_ENABLED` env var independently (it cannot import `swiss_ai_hub`).
    """

    model_config = EnvironmentSettings.create_settings_config("RAG_IMAGE_INLINE_")

    ENABLED: Annotated[bool, Field(description="Whether RAG figures are inlined as base64 at the LiteLLM gateway.")] = (
        True
    )

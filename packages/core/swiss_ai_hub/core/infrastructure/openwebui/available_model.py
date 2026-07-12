from typing import Annotated

from pydantic import BaseModel, Field


class AvailableModel(BaseModel):
    """LLM chat model exposed by LiteLLM and eligible for OpenWebUI provisioning."""

    capability: Annotated[str, Field(description="Capability segment of the model name, e.g. 'text-generation'")]
    name: Annotated[str, Field(description="Model name without the capability prefix, e.g. 'gemma-4-31B-it'")]
    display_name: Annotated[str, Field(description="Human-readable name shown in OpenWebUI")]

    @property
    def litellm_name(self) -> str:
        """Full LiteLLM model name (``capability/name``) — used as the workspace model's base_model_id."""
        return f"{self.capability}/{self.name}"

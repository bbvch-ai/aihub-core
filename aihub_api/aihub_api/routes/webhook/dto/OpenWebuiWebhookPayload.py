import json
from typing import Annotated

from pydantic import BaseModel, Field, field_validator

from aihub_api.routes.webhook.dto.OpenWebuiWebhookUser import OpenWebuiWebhookUser


class OpenWebuiWebhookPayload(BaseModel):
    action: Annotated[str, Field(description="OpenWebUI webhook action type (e.g. 'signup', 'login')")]
    message: Annotated[str, Field(default="")]
    user: Annotated[OpenWebuiWebhookUser, Field(default_factory=OpenWebuiWebhookUser)]

    @field_validator("user", mode="before")
    @classmethod
    def parse_user_json(cls, v: str | dict) -> dict:
        """OpenWebUI sends user as a JSON string via model_dump_json()."""
        if isinstance(v, str):
            return json.loads(v)
        return v

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field


class OpenWebuiWebhookUser(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: Annotated[str, Field(default="")]
    email: Annotated[str, Field(default="")]
    name: Annotated[str, Field(default="")]
    role: Annotated[str, Field(default="")]

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field


class OpenWebuiWebhookUser(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: Annotated[str, Field(description="OpenWebUI user ID")] = ""
    email: Annotated[str, Field(description="User email address")] = ""
    name: Annotated[str, Field(description="User display name")] = ""
    role: Annotated[str, Field(description="OpenWebUI role")] = ""

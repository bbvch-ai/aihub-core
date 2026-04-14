from typing import Annotated

from pydantic import BaseModel, Field


class WebhookResponse(BaseModel):
    status: Annotated[str, Field(description="Webhook processing result status")]

from datetime import datetime
from typing import Annotated, Self

from pydantic import BaseModel, Field
from swiss_ai_hub.core.persistence import BearerToken


class CreateTokenResponse(BaseModel):
    id: Annotated[str, Field(description="The token ID", example="603d2f9c8a86f9b7f0e8f3c9")]
    name: Annotated[str, Field(description="The name of the API token", example="My API Token")]
    expiry_date: Annotated[datetime, Field(description="Expiry date")]
    token: Annotated[str, Field(description="The generated API token, only returned at creation")]

    @classmethod
    def from_entity(cls, token: BearerToken) -> Self:
        return cls(id=str(token.id), name=token.name, expiry_date=token.expiry_date, token=token.token)

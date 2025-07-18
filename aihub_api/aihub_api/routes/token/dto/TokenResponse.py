from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, Field


class TokenResponse(BaseModel):
    id: Annotated[str, Field(description="The token ID", example="603d2f9c8a86f9b7f0e8f3c9")]
    name: Annotated[str, Field(description="The name of the API token", example="My API Token")]
    expiry_date: Annotated[datetime, Field(description="Expiry date")]
    roles: Annotated[list[str], Field(description="List of roles granted to the access token")]

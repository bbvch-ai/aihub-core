from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, Field


class CreateTokenResponse(BaseModel):
    id: Annotated[str, Field(description="The token ID", example="603d2f9c8a86f9b7f0e8f3c9")]
    name: Annotated[str, Field(description="The name of the API token", example="My API Token")]
    expiry_date: Annotated[datetime, Field(description="Expiry date")]
    token: Annotated[str, Field(description="The generated API token, only returned at creation")]

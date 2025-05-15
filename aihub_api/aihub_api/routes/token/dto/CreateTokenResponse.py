from datetime import datetime

from pydantic import BaseModel, Field


class CreateTokenResponse(BaseModel):
    id: str = Field(..., description="The token ID", example="603d2f9c8a86f9b7f0e8f3c9")
    name: str = Field(..., example="My API Token")
    expiry_date: datetime = Field(..., description="Expiry date")
    token: str = Field(..., description="The generated API token, only returned at creation")

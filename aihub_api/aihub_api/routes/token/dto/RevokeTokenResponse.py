from pydantic import BaseModel, Field


class RevokeTokenResponse(BaseModel):
    detail: str = Field(..., example="Token revoked successfully.")

from typing import Annotated

from pydantic import BaseModel, Field


class RevokeTokenResponse(BaseModel):
    detail: Annotated[str, Field(example="Token revoked successfully.")]

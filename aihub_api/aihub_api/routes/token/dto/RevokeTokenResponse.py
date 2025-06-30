from typing import Annotated

from pydantic import BaseModel, Field


class RevokeTokenResponse(BaseModel):
    detail: Annotated[
        str, Field(description="Status message about the token revocation", example="Token revoked successfully.")
    ]

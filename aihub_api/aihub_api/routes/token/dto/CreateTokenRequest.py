from datetime import datetime, timezone
from typing import List

from pydantic import BaseModel, Field, constr, field_validator


class CreateTokenRequest(BaseModel):
    name: constr(min_length=1, max_length=100, strip_whitespace=True) = Field(
        ..., example="My API Token", description="Token name between 1 and 100 characters"
    )
    expiry_date: datetime = Field(
        ..., description="Expiry date in ISO format (must be in the future)", example="2025-12-31T23:59:59Z"
    )
    roles: List[constr(min_length=1, strip_whitespace=True)] = Field(
        ..., min_items=1, description="Non-empty list of roles associated with the token", example=["read", "write"]
    )

    @field_validator("expiry_date")
    @classmethod
    def expiry_date_must_be_future(cls, v: datetime) -> datetime:
        if v.tzinfo is None:  # If datetime is naive, assume UTC
            v = v.replace(tzinfo=timezone.utc)

        if v <= datetime.now(timezone.utc):
            raise ValueError("Expiry date must be in the future")
        return v

    @field_validator("roles")
    @classmethod
    def roles_must_be_unique(cls, v: List[str]) -> List[str]:
        if len(set(v)) != len(v):
            raise ValueError("Roles must be unique")
        return v

    model_config = {
        "json_schema_extra": {
            "example": {"name": "My API Token", "expiry_date": "2025-12-31T23:59:59Z", "roles": ["read", "write"]}
        }
    }

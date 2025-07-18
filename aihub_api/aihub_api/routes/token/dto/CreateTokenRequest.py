from datetime import UTC, datetime
from typing import Annotated

from pydantic import BaseModel, Field, field_validator
from pydantic.types import StringConstraints


class CreateTokenRequest(BaseModel):
    name: Annotated[
        str,
        StringConstraints(min_length=1, max_length=100, strip_whitespace=True),
        Field(example="My API Token", description="Token name between 1 and 100 characters"),
    ]
    expiry_date: Annotated[
        datetime, Field(description="Expiry date in ISO format (must be in the future)", example="2025-12-31T23:59:59Z")
    ]

    @field_validator("expiry_date")
    @classmethod
    def expiry_date_must_be_future(cls, v: datetime) -> datetime:
        if v.tzinfo is None:  # If datetime is naive, assume UTC
            v = v.replace(tzinfo=UTC)

        if v <= datetime.now(UTC):
            raise ValueError("Expiry date must be in the future")
        return v

    model_config = {
        "json_schema_extra": {
            "example": {"name": "My API Token", "expiry_date": "2025-12-31T23:59:59Z", "roles": ["read", "write"]}
        }
    }

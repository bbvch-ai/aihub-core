from datetime import UTC, datetime
from typing import Annotated, Self

from pydantic import BaseModel, Field, field_validator
from swiss_ai_hub.core.persistence import BearerToken


class TokenResponse(BaseModel):
    id: Annotated[str, Field(description="The token ID", example="603d2f9c8a86f9b7f0e8f3c9")]
    name: Annotated[str, Field(description="The name of the API token", example="My API Token")]
    created_at: Annotated[datetime, Field(description="When the token was created")]
    expiry_date: Annotated[datetime, Field(description="Expiry date")]
    last_used_at: Annotated[
        datetime | None,
        Field(description="When the token last authenticated a request, to within five minutes; null if never"),
    ]

    @field_validator("created_at", "expiry_date", "last_used_at")
    @classmethod
    def mark_as_utc(cls, value: datetime | None) -> datetime | None:
        """MongoEngine returns naive UTC datetimes, which a browser would read as local time."""
        if value is None or value.tzinfo is not None:
            return value
        return value.replace(tzinfo=UTC)

    @classmethod
    def from_entity(cls, token: BearerToken) -> Self:
        return cls(
            id=str(token.id),
            name=token.name,
            created_at=token.created_at,
            expiry_date=token.expiry_date,
            last_used_at=token.last_used_at,
        )

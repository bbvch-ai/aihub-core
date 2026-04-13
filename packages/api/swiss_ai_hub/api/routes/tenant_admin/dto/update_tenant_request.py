from typing import Annotated

from pydantic import BaseModel, Field, field_validator
from swiss_ai_hub.core.auth.access.access_checker import AccessChecker


class UpdateTenantRequest(BaseModel):
    """Request model for updating a tenant. All fields are optional."""

    name: Annotated[str | None, Field(description="The unique display name of the tenant.")] = None
    description: Annotated[str | None, Field(description="A short description of the tenant.")] = None
    access_rules: Annotated[list[str] | None, Field(description="Access rules granted to this tenant.")] = None

    @field_validator("access_rules")
    @classmethod
    def validate_access_rules(cls, value: list[str] | None) -> list[str] | None:
        if value is None:
            return value
        for rule in value:
            if not AccessChecker.validate_user_access_rule(rule):
                raise ValueError(f"Invalid access rule: {rule!r}")
        return value

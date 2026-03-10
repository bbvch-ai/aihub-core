from typing import Annotated

from pydantic import BaseModel, Field, field_validator
from swiss_ai_hub.core.auth.access.AccessChecker import AccessChecker

from swiss_ai_hub.api.routes.role.dto.UsageLimitDTO import UsageLimitDTO


class CreateRoleRequest(BaseModel):
    """Request model for creating a new role."""

    name: Annotated[str, Field(description="The unique name of the role.")]
    description: Annotated[str, Field(description="A short description of the role's purpose.")]
    access_rules: Annotated[list[str], Field(description="A list of access rules granted by this role.")] = []
    usage_limits: Annotated[list[UsageLimitDTO], Field(description="Pattern-based usage limit rules.")] = []

    @field_validator("access_rules")
    @classmethod
    def validate_access_rules(cls, value: list[str]) -> list[str]:
        for rule in value:
            if not AccessChecker.validate_user_access_rule(rule):
                raise ValueError(f"Invalid access rule: {rule!r}")
        return value

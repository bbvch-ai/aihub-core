from typing import Annotated

from aihub_lib.auth.access.AccessChecker import AccessChecker
from pydantic import BaseModel, Field, field_validator

from aihub_api.routes.role.dto.UsageLimitDTO import UsageLimitDTO


class UpdateRoleRequest(BaseModel):
    """Request model for updating an existing role. All fields are optional."""

    name: Annotated[str | None, Field(description="The new unique name of the role.")] = None
    description: Annotated[str | None, Field(description="The new description for the role.")] = None
    access_rules: Annotated[list[str] | None, Field(description="The new list of access rules.")] = None
    usage_limits: Annotated[list[UsageLimitDTO] | None, Field(description="Pattern-based usage limit rules.")] = None

    @field_validator("access_rules")
    @classmethod
    def validate_access_rules(cls, value: list[str] | None) -> list[str] | None:
        if value is None:
            return None
        for rule in value:
            if not AccessChecker.validate_user_access_rule(rule):
                raise ValueError(f"Invalid access rule: {rule!r}")
        return value

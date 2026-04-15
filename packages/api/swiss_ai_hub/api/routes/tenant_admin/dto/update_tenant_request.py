from typing import Annotated

from pydantic import BaseModel, Field, field_validator
from swiss_ai_hub.core.auth.access.access_checker import AccessChecker

from swiss_ai_hub.api.routes.tenant_admin.dto.tenant_field_constraints import (
    TenantDescription,
    TenantName,
)


class UpdateTenantRequest(BaseModel):
    """Request model for updating a tenant. All fields are optional."""

    name: TenantName | None = None
    description: TenantDescription | None = None
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

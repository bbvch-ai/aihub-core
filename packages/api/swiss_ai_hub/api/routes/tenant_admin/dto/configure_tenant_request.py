from typing import Annotated

from pydantic import BaseModel, Field, field_validator
from swiss_ai_hub.core.auth.access.access_checker import AccessChecker

from swiss_ai_hub.api.routes.tenant_admin.dto.tenant_field_constraints import (
    TenantDescription,
    TenantId,
    TenantName,
)


class ConfigureTenantRequest(BaseModel):
    """Request model for attaching metadata to an existing Keycloak tenant group.

    The `tenant_id` must match an existing Keycloak group under `/tenants/`. Use the
    `/admin/tenants/unconfigured` endpoint to list available tenant IDs.
    """

    tenant_id: TenantId
    name: TenantName
    description: TenantDescription = ""
    access_rules: Annotated[list[str], Field(description="Access rules granted to this tenant.")] = []

    @field_validator("access_rules")
    @classmethod
    def validate_access_rules(cls, value: list[str]) -> list[str]:
        for rule in value:
            if not AccessChecker.validate_user_access_rule(rule):
                raise ValueError(f"Invalid access rule: {rule!r}")
        return value

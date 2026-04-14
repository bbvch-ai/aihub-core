from typing import Annotated

from pydantic import BaseModel, Field, field_validator
from swiss_ai_hub.core.auth.access.access_checker import AccessChecker


class ConfigureTenantRequest(BaseModel):
    """Request model for attaching metadata to an existing Keycloak tenant group.

    The `tenant_id` must match an existing Keycloak group under `/tenants/`. Use the
    `/admin/tenants/unconfigured` endpoint to list available tenant IDs.
    """

    tenant_id: Annotated[
        str,
        Field(description="Keycloak tenant group name to configure (must already exist in Keycloak)."),
    ]
    name: Annotated[str, Field(description="The unique display name of the tenant.")]
    description: Annotated[str, Field(description="A short description of the tenant.")] = ""
    access_rules: Annotated[list[str], Field(description="Access rules granted to this tenant.")] = []

    @field_validator("access_rules")
    @classmethod
    def validate_access_rules(cls, value: list[str]) -> list[str]:
        for rule in value:
            if not AccessChecker.validate_user_access_rule(rule):
                raise ValueError(f"Invalid access rule: {rule!r}")
        return value

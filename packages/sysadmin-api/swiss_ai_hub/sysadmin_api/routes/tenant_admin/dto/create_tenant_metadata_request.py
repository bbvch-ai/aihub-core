# SPDX-License-Identifier: LicenseRef-Proprietary
from typing import Annotated

from pydantic import BaseModel, Field, StringConstraints, field_validator
from swiss_ai_hub.core.auth.access.access_checker import AccessChecker


class CreateTenantMetadataRequest(BaseModel):
    """Request model for attaching metadata to an existing Keycloak tenant group.

    ``tenant_id`` is not user-chosen here — it must already exist as a Keycloak group
    under ``/tenants/``. Use the ``/admin/tenants/unconfigured`` endpoint to list
    configurable ids. A regex constraint is deliberately avoided because Keycloak
    accepts group names this layer would otherwise reject (e.g. ``MyTenant``,
    ``customer.acme``); the only checks that belong here are a minimum length (reject
    empty payloads) and a maximum length matching Keycloak's group-name cap (DoS guard
    against unbounded strings reaching Mongo).
    """

    tenant_id: Annotated[
        str,
        Field(
            description="Keycloak tenant group name (must already exist under /tenants/).",
            min_length=1,
            max_length=255,
        ),
    ]
    name: Annotated[
        str,
        StringConstraints(strip_whitespace=True, min_length=1, max_length=120),
        Field(description="The unique display name of the tenant."),
    ]
    description: Annotated[
        str,
        StringConstraints(max_length=500),
        Field(description="A short description of the tenant."),
    ] = ""
    access_rules: Annotated[list[str], Field(description="Access rules granted to this tenant.")] = []

    @field_validator("access_rules")
    @classmethod
    def validate_access_rules(cls, value: list[str]) -> list[str]:
        for rule in value:
            if not AccessChecker.validate_user_access_rule(rule):
                raise ValueError(f"Invalid access rule: {rule!r}")
        return value

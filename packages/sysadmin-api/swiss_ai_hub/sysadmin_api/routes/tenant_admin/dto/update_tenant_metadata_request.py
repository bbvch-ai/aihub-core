# SPDX-License-Identifier: LicenseRef-Proprietary
from typing import Annotated

from pydantic import BaseModel, Field, StringConstraints, field_validator
from swiss_ai_hub.core.auth.access.access_checker import AccessChecker


class UpdateTenantMetadataRequest(BaseModel):
    """Request model for updating a tenant. All fields are optional.

    Name and description constraints mirror ``CreateTenantMetadataRequest`` — an update
    must not be able to slip a value past a constraint that create enforced.
    """

    name: (
        Annotated[
            str,
            StringConstraints(strip_whitespace=True, min_length=1, max_length=120),
            Field(description="The unique display name of the tenant."),
        ]
        | None
    ) = None
    description: (
        Annotated[
            str,
            StringConstraints(max_length=500),
            Field(description="A short description of the tenant."),
        ]
        | None
    ) = None
    access_rules: Annotated[list[str] | None, Field(description="Access rules granted to this tenant.")] = None

    @field_validator("access_rules")
    @classmethod
    def validate_access_rules(cls, value: list[str] | None) -> list[str] | None:
        for rule in value or []:
            if not AccessChecker.validate_user_access_rule(rule):
                raise ValueError(f"Invalid access rule: {rule!r}")
        return value

from typing import Annotated

from pydantic import BaseModel, Field, field_validator
from swiss_ai_hub.core.auth.access.access_checker import AccessChecker


class AccessCapabilitiesRequest(BaseModel):
    access_rules: Annotated[
        list[str], Field(description="Draft access rules to evaluate the capability catalog against.")
    ]
    restrict_to_tenant: Annotated[
        bool,
        Field(
            description="Hide capabilities the acting tenant's ceiling cannot grant (role editor). "
            "Set false when editing the tenant ceiling itself (sysadmin)."
        ),
    ] = True

    @field_validator("access_rules")
    @classmethod
    def _drop_invalid_rules(cls, access_rules: list[str]) -> list[str]:
        return [rule for rule in access_rules if AccessChecker.validate_user_access_rule(rule)]

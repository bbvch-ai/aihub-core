from typing import Annotated, Any, Literal

from pydantic import Field

from swiss_ai_hub.core.auth.access.access_checker import AccessChecker
from swiss_ai_hub.core.form.base.config_authorization_violation import ConfigAuthorizationViolation
from swiss_ai_hub.core.form.elements.input_text import InputText
from swiss_ai_hub.core.i18n.locale_handler import LocaleHandler


class OrgMemoryTenantInput(InputText):
    """Text input for the organization-memory `tenant_id` field that also enforces
    config-time access control.

    Renders identically to a plain `InputText` (same UI), but its presence in a
    submitted config means the section is enabled — so we require the configuring user
    to hold `aihub.user.memory.organization`. When the parent `org_memory` section is
    null the walker never reaches this element, so no check fires.
    """

    formkit: Annotated[
        Literal["orgMemoryTenantInput"],
        Field(description="Organization-memory tenant_id input element."),
    ] = "orgMemoryTenantInput"

    def validate_authorization(
        self, field_path: str, value: Any, access_checker: AccessChecker, t: LocaleHandler
    ) -> list[ConfigAuthorizationViolation]:
        if value is None:
            return []
        if access_checker.has_access("aihub.user.memory.organization.?>"):
            return []
        return [
            ConfigAuthorizationViolation(
                field=field_path,
                resource_type="organization_memory",
                resource="organization_memory",
                message=t("lib.common.authorization.no_access_organization_memory"),
            )
        ]

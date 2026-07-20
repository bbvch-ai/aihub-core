from typing import Annotated, Any, Literal, Self

from pydantic import Field

from swiss_ai_hub.core.auth.access.access_checker import AccessChecker
from swiss_ai_hub.core.form.base.config_authorization_violation import ConfigAuthorizationViolation
from swiss_ai_hub.core.form.base.prime_vue_element import PrimeVueElement
from swiss_ai_hub.core.i18n.locale_handler import LocaleHandler
from swiss_ai_hub.core.i18n.locale_string import LocaleString


class TenantSelect(PrimeVueElement):
    """
    A FormKit element for selecting one of the tenants the user belongs to.

    Renders as a select dropdown listing tenant *names*, while the submitted value is the
    tenant *id*. The frontend populates the options from the user's memberships and
    pre-selects their active tenant.

    ### Form Duality

    ```python
    class MyConfig(Form):
        tenant_id: Annotated[
            str | TenantSelect,
            Field(description="Tenant to scope against"),
        ]

        @classmethod
        def as_form(cls) -> "MyConfig":
            return cls(
                tenant_id=TenantSelect(
                    label=LocaleString(en="Tenant"),
                ),
            )

    # Data mode - from submission:
    config = MyConfig(tenant_id="507f1f77bcf86cd799439011")
    ```
    """

    formkit: Annotated[Literal["tenantSelect"], Field(description="Tenant select element.")] = "tenantSelect"

    placeholder: Annotated[LocaleString | str | None, Field(description="Placeholder text")] = None
    filter: Annotated[bool, Field(description="Whether to enable filtering/search")] = True

    def in_locale(self, t: LocaleHandler) -> Self:
        self_copy = super().in_locale(t)
        if isinstance(self_copy.placeholder, LocaleString):
            self_copy.placeholder = t.extract(self_copy.placeholder)
        return self_copy

    def validate_authorization(
        self,
        field_path: str,
        value: Any,
        access_checker: AccessChecker,
        accessible_tenant_ids: set[str],
        t: LocaleHandler,
    ) -> list[ConfigAuthorizationViolation]:
        """Membership is not expressible as an access rule — `access_checker` only carries the rules
        of the tenant the user is acting within — so it is checked against the caller-resolved
        membership set instead."""
        if not isinstance(value, str):
            return []
        if access_checker.is_sys_admin or value in accessible_tenant_ids:
            return []
        return [
            ConfigAuthorizationViolation(
                field=field_path,
                resource_type="tenant",
                resource=value,
                message=t("lib.common.authorization.no_access_tenant", tenant=value),
            )
        ]

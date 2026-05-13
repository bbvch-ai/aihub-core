from typing import Annotated, Self

from pydantic import Field, model_validator

from swiss_ai_hub.core.form import ChipsInput, InputText, OrgMemoryTenantInput
from swiss_ai_hub.core.form.base.formkit_element import FormkitElement
from swiss_ai_hub.core.form.form import Form
from swiss_ai_hub.core.generative_ai.memory.memory_settings import MemorySettings
from swiss_ai_hub.core.i18n.locale_string import LocaleString


class OrgMemoryWriteConfig(Form):
    """Tenant + namespace scoping for organization-memory writes (and base for read-side scoping)."""

    tenant_id: Annotated[
        str | OrgMemoryTenantInput,
        Field(description="Tenant ID for organization-memory scoping."),
    ] = Field(default_factory=lambda: MemorySettings().DEFAULT_TENANT_ID)
    default_tenant_namespace: Annotated[
        str | InputText | None,
        Field(
            description=(
                "Default namespace used when a start event omits an override. Writes are singular — "
                "only one namespace can be the write target."
            ),
        ),
    ] = Field(default_factory=lambda: MemorySettings().DEFAULT_TENANT_NAMESPACE)
    allowed_tenant_namespaces: Annotated[
        list[str] | ChipsInput,
        Field(
            description=(
                "Allow-list of namespaces. Empty = unrestricted. Controls the read scope and validates "
                "the effective write namespace."
            ),
        ),
    ] = []

    @model_validator(mode="after")
    def _validate_default_in_allowed(self) -> Self:
        """Ensure `default_tenant_namespace` is consistent with `allowed_tenant_namespaces`.

        Skipped in form mode (when either field still holds a FormkitElement)."""
        if isinstance(self.allowed_tenant_namespaces, FormkitElement):
            return self
        if isinstance(self.default_tenant_namespace, FormkitElement):
            return self
        allowed = self.allowed_tenant_namespaces
        default = self.default_tenant_namespace
        if allowed and default is not None and default not in allowed:
            raise ValueError(f"default_tenant_namespace={default!r} is not in allowed_tenant_namespaces={allowed!r}")
        return self

    @classmethod
    def as_form(cls) -> Self:
        """Factory method to create a form-mode OrgMemoryWriteConfig."""
        return cls(
            tenant_id=OrgMemoryTenantInput(
                label=LocaleString.from_i18n_path("lib.org_memory.tenant_id.label"),
                help=LocaleString.from_i18n_path("lib.org_memory.tenant_id.help"),
            ),
            default_tenant_namespace=InputText(
                label=LocaleString.from_i18n_path("lib.org_memory.default_tenant_namespace.label"),
                help=LocaleString.from_i18n_path("lib.org_memory.default_tenant_namespace.help"),
            ),
            allowed_tenant_namespaces=ChipsInput(
                label=LocaleString.from_i18n_path("lib.org_memory.allowed_tenant_namespaces.label"),
                help=LocaleString.from_i18n_path("lib.org_memory.allowed_tenant_namespaces.help"),
                placeholder=LocaleString.from_i18n_path("lib.org_memory.allowed_tenant_namespaces.placeholder"),
            ),
        )

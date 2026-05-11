from typing import Annotated, Self

from pydantic import Field

from swiss_ai_hub.core.form import InputText
from swiss_ai_hub.core.form.form import Form
from swiss_ai_hub.core.generative_ai.memory.memory_settings import MemorySettings
from swiss_ai_hub.core.generative_ai.memory.tenant_namespace_entry import TenantNamespaceEntry
from swiss_ai_hub.core.i18n.locale_string import LocaleString


class OrgMemoryWriteConfig(Form):
    """Tenant + namespace scoping for organization-memory writes (and base for read-side scoping)."""

    tenant_id: Annotated[
        str | InputText,
        Field(description="Tenant ID for organization-memory scoping."),
    ] = Field(default_factory=lambda: MemorySettings().DEFAULT_TENANT_ID)
    default_tenant_namespace: Annotated[
        str | InputText | None,
        Field(description="Default namespace used when a start event omits an override."),
    ] = Field(default_factory=lambda: MemorySettings().DEFAULT_TENANT_NAMESPACE)
    allowed_tenant_namespaces: Annotated[
        list[TenantNamespaceEntry],
        Field(
            description=(
                "Allow-list of namespaces. Empty = unrestricted. Controls the read scope and validates "
                "the effective write namespace."
            ),
        ),
    ] = []

    @property
    def allowed_tenant_namespace_values(self) -> list[str]:
        """Returns the allow-list as a plain list of namespace strings."""
        return [entry.name for entry in self.allowed_tenant_namespaces]

    @classmethod
    def as_form(cls) -> Self:
        """Factory method to create a form-mode OrgMemoryWriteConfig."""
        return cls(
            tenant_id=InputText(
                label=LocaleString.from_i18n_path("lib.org_memory.tenant_id.label"),
                help=LocaleString.from_i18n_path("lib.org_memory.tenant_id.help"),
            ),
            default_tenant_namespace=InputText(
                label=LocaleString.from_i18n_path("lib.org_memory.default_tenant_namespace.label"),
                help=LocaleString.from_i18n_path("lib.org_memory.default_tenant_namespace.help"),
            ),
            allowed_tenant_namespaces=[TenantNamespaceEntry.as_form()],
        )

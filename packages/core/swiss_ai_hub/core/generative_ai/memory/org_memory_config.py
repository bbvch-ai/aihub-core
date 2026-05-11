from typing import Annotated, Self

from pydantic import Field

from swiss_ai_hub.core.form import Checkbox, InputText
from swiss_ai_hub.core.form.form import Form
from swiss_ai_hub.core.generative_ai.memory.memory_settings import MemorySettings
from swiss_ai_hub.core.i18n.locale_string import LocaleString


class OrgMemoryConfig(Form):
    """Tenant + namespace scoping and toggles for organization-memory reads and writes."""

    rerank_organization_memory: Annotated[
        bool | Checkbox,
        Field(description="Whether to rerank organization-memory search results via the configured reranker."),
    ] = True
    tenant_id: Annotated[
        str,
        Field(description="Tenant ID for organization-memory scoping."),
    ] = Field(default_factory=lambda: MemorySettings().DEFAULT_TENANT_ID)
    default_tenant_namespace: Annotated[
        str | InputText | None,
        Field(description="Default namespace used when a start event omits an override."),
    ] = Field(default_factory=lambda: MemorySettings().DEFAULT_TENANT_NAMESPACE)
    allowed_tenant_namespaces: Annotated[
        list[str],
        Field(
            description=(
                "Allow-list of namespaces. Empty = unrestricted. Controls the read scope and validates "
                "the effective write namespace."
            ),
        ),
    ] = []

    @classmethod
    def as_form(cls) -> Self:
        """Factory method to create a form-mode OrgMemoryConfig."""
        return cls(
            rerank_organization_memory=Checkbox(
                label=LocaleString.from_i18n_path("lib.org_memory.rerank_organization_memory.label"),
                help=LocaleString.from_i18n_path("lib.org_memory.rerank_organization_memory.help"),
            ),
            default_tenant_namespace=InputText(
                label=LocaleString.from_i18n_path("lib.org_memory.default_tenant_namespace.label"),
                help=LocaleString.from_i18n_path("lib.org_memory.default_tenant_namespace.help"),
            ),
        )

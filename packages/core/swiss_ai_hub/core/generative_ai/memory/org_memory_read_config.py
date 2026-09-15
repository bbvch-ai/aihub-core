from typing import Annotated, Self

from pydantic import Field

from swiss_ai_hub.core.form.elements.checkbox import Checkbox
from swiss_ai_hub.core.form.elements.chips_input import ChipsInput
from swiss_ai_hub.core.form.elements.input_text import InputText
from swiss_ai_hub.core.form.elements.tenant_select import TenantSelect
from swiss_ai_hub.core.generative_ai.memory.org_memory_write_config import OrgMemoryWriteConfig
from swiss_ai_hub.core.i18n.locale_string import LocaleString


class OrgMemoryReadConfig(OrgMemoryWriteConfig):
    """Extends OrgMemoryWriteConfig with read-side toggles (reranking)."""

    rerank_organization_memory: Annotated[
        bool | Checkbox,
        Field(description="Whether to rerank organization-memory search results via the configured reranker."),
    ] = True

    @classmethod
    def as_form(cls) -> Self:
        """Factory method to create a form-mode OrgMemoryReadConfig."""
        return cls(
            tenant_id=TenantSelect(
                label=LocaleString.from_i18n_path("lib.org_memory.tenant_id.label"),
                help=LocaleString.from_i18n_path("lib.org_memory.tenant_id.help"),
                placeholder=LocaleString.from_i18n_path("lib.org_memory.tenant_id.placeholder"),
            ),
            default_tenant_namespace=InputText(
                label=LocaleString.from_i18n_path("lib.org_memory.default_tenant_namespace.label"),
                help=LocaleString.from_i18n_path("lib.org_memory.default_tenant_namespace.help"),
                additional_validation_rules=cls.DEFAULT_NAMESPACE_FORM_RULE,
            ),
            allowed_tenant_namespaces=ChipsInput(
                label=LocaleString.from_i18n_path("lib.org_memory.allowed_tenant_namespaces.label"),
                help=LocaleString.from_i18n_path("lib.org_memory.allowed_tenant_namespaces.help"),
                placeholder=LocaleString.from_i18n_path("lib.org_memory.allowed_tenant_namespaces.placeholder"),
            ),
            rerank_organization_memory=Checkbox(
                label=LocaleString.from_i18n_path("lib.org_memory.rerank_organization_memory.label"),
                help=LocaleString.from_i18n_path("lib.org_memory.rerank_organization_memory.help"),
            ),
        )

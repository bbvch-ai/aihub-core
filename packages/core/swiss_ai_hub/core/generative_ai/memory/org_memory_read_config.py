from typing import Annotated, Self

from pydantic import Field

from swiss_ai_hub.core.form import Checkbox, InputText
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
            tenant_id=InputText(
                label=LocaleString.from_i18n_path("lib.org_memory.tenant_id.label"),
                help=LocaleString.from_i18n_path("lib.org_memory.tenant_id.help"),
            ),
            default_tenant_namespace=InputText(
                label=LocaleString.from_i18n_path("lib.org_memory.default_tenant_namespace.label"),
                help=LocaleString.from_i18n_path("lib.org_memory.default_tenant_namespace.help"),
            ),
            rerank_organization_memory=Checkbox(
                label=LocaleString.from_i18n_path("lib.org_memory.rerank_organization_memory.label"),
                help=LocaleString.from_i18n_path("lib.org_memory.rerank_organization_memory.help"),
            ),
        )

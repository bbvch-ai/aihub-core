from typing import Annotated, ClassVar, Self

from pydantic import Field

from swiss_ai_hub.core.form.elements.chips_input import ChipsInput
from swiss_ai_hub.core.form.elements.input_text import InputText
from swiss_ai_hub.core.form.elements.tenant_select import TenantSelect
from swiss_ai_hub.core.form.form import Form
from swiss_ai_hub.core.generative_ai.memory.memory_settings import MemorySettings
from swiss_ai_hub.core.i18n.locale_string import LocaleString


class OrgMemoryWriteConfig(Form):
    """Tenant + namespace scoping for organization-memory writes (and base for read-side scoping).

    A `default_tenant_namespace` outside `allowed_tenant_namespaces` is deliberately NOT a config-level
    error. The API validates submissions against a JSON Schema rebuilt from this model, which cannot carry
    cross-field rules, so such a config saves either way — and raising here would instead abort
    `AgentConfig.model_validate` on every dispatched event, bricking the whole agent with no visible error.
    `OrgMemoryNamespaceResolver.resolve_for_write` enforces the rule inside a step, where the dispatcher
    turns it into an `ExceptionEvent` the user can see. `DEFAULT_NAMESPACE_FORM_RULE` gives admins the same
    feedback in the form.
    """

    required_access_rule: ClassVar[str] = "aihub.user.memory.organization.?>"
    required_access_rule_message_path: ClassVar[str] = "lib.common.authorization.no_access_organization_memory"

    DEFAULT_NAMESPACE_FORM_RULE: ClassVar[str] = "memberOf:allowed_tenant_namespaces"

    tenant_id: Annotated[
        str | TenantSelect,
        Field(description="Tenant ID for organization-memory scoping."),
    ] = Field(default_factory=lambda: MemorySettings().DEFAULT_TENANT_ID)
    default_tenant_namespace: Annotated[
        str | InputText | None,
        Field(
            description=(
                "Default namespace used when a start event omits an override. Writes are singular — "
                "only one namespace can be the write target. A default outside the allow-list is "
                "rejected when a write actually resolves it, not when the config is built."
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

    @classmethod
    def as_form(cls) -> Self:
        """Factory method to create a form-mode OrgMemoryWriteConfig."""
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
        )

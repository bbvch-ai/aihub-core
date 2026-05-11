from typing import Annotated, Self

from pydantic import Field

from swiss_ai_hub.core.form import InputText
from swiss_ai_hub.core.form.form import Form
from swiss_ai_hub.core.i18n.locale_string import LocaleString


class TenantNamespaceEntry(Form):
    """A single entry in an org-memory namespace allow-list (wrapper to enable Repeater rendering)."""

    name: Annotated[
        str | InputText,
        Field(description="Namespace value."),
    ] = ""

    @classmethod
    def as_form(cls) -> Self:
        return cls(
            name=InputText(
                label=LocaleString.from_i18n_path("lib.org_memory.allowed_tenant_namespaces.entry.label"),
                help=LocaleString.from_i18n_path("lib.org_memory.allowed_tenant_namespaces.entry.help"),
            ),
        )

from typing import Annotated, Any, Literal, Self

from pydantic import Field

from swiss_ai_hub.core.form.base.PrimeVueElement import PrimeVueElement
from swiss_ai_hub.core.i18n.LocaleHandler import LocaleHandler
from swiss_ai_hub.core.i18n.LocaleString import LocaleString


class Listbox(PrimeVueElement):
    """https://formkit-primevue.netlify.app/inputs/Listbox"""

    formkit: Annotated[Literal["primeListbox"], Field(description="PrimeVue Listbox element.")] = "primeListbox"
    disabled: Annotated[bool, Field(description="Whether the input is disabled")] = False
    readonly: Annotated[bool, Field(description="Whether the input is readonly")] = False
    placeholder: Annotated[LocaleString | str | None, Field(description="Placeholder text")] = None
    options: Annotated[list[dict[str, Any]], Field(description="Array of selectable option objects")]
    option_label: Annotated[
        str | None, Field(description="Property name to use as the label of an option", alias="optionLabel")
    ] = None
    option_value: Annotated[
        str | None, Field(description="Property name to use as the value of an option", alias="optionValue")
    ] = None
    multiple: Annotated[bool, Field(description="Whether to allow multiple selections")] = False
    filter: Annotated[bool, Field(description="Whether to enable filtering")] = False

    def in_locale(self, t: LocaleHandler) -> Self:
        self_copy = super().in_locale(t)
        if isinstance(self_copy.placeholder, LocaleString):
            self_copy.placeholder = t.extract(self_copy.placeholder)
        return self_copy

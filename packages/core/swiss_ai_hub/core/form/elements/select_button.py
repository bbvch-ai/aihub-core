from typing import Annotated, Literal, Self

from pydantic import Field

from swiss_ai_hub.core.form.base.prime_vue_element import PrimeVueElement
from swiss_ai_hub.core.i18n.locale_handler import LocaleHandler
from swiss_ai_hub.core.i18n.locale_string import LocaleString


class SelectButton(PrimeVueElement):
    """https://formkit-primevue.netlify.app/inputs/SelectButton"""

    formkit: Annotated[Literal["primeSelectButton"], Field(description="PrimeVue SelectButton element.")] = (
        "primeSelectButton"
    )

    options: Annotated[
        list[str | LocaleString | dict[str, str | LocaleString]] | list[str],
        Field(description="Array of selectable options (objects or strings)"),
    ]
    option_label: Annotated[
        str | None, Field(description="Property name to use as the label of an option", alias="optionLabel")
    ] = None
    option_value: Annotated[
        str | None, Field(description="Property name to use as the value of an option", alias="optionValue")
    ] = None

    disabled: Annotated[bool, Field(description="Whether the input is disabled")] = False
    readonly: Annotated[bool, Field(description="Whether the input is readonly")] = False
    option_disabled: Annotated[
        str | None, Field(description="Property name to use as the disabled flag of an option", alias="optionDisabled")
    ] = None
    multiple: Annotated[bool, Field(description="Whether to allow multiple selections")] = False
    unselectable: Annotated[bool, Field(description="Whether selection can be cleared")] = True
    data_key: Annotated[
        str | None, Field(description="Property name for unique option identification", alias="dataKey")
    ] = None

    def in_locale(self, t: LocaleHandler) -> Self:
        self_copy = super().in_locale(t)
        for option in self_copy.options:
            if isinstance(option, str):
                continue
            if isinstance(option, LocaleString):
                option = t.extract(option)
            if isinstance(option[self.option_label], LocaleString):
                option[self.option_label] = t.extract(option[self.option_label])
        return self_copy

from typing import Annotated, Any, Literal, Self

from pydantic import Field

from swiss_ai_hub.core.form.base.PrimeVueElement import PrimeVueElement
from swiss_ai_hub.core.i18n.LocaleHandler import LocaleHandler


class RadioButton(PrimeVueElement):
    """https://formkit-primevue.netlify.app/inputs/RadioButton"""

    formkit: Annotated[Literal["primeRadioButton"], Field(description="PrimeVue RadioButton element.")] = (
        "primeRadioButton"
    )
    disabled: Annotated[bool, Field(description="Whether the input is disabled")] = False
    readonly: Annotated[bool, Field(description="Whether the input is readonly")] = False
    options: Annotated[list[dict[str, Any]], Field(description="Array of selectable option objects")]
    option_label: Annotated[
        str | None, Field(description="Property name to use as the label of an option", alias="optionLabel")
    ] = None
    option_value: Annotated[
        str | None, Field(description="Property name to use as the value of an option", alias="optionValue")
    ] = None
    option_class: Annotated[str | None, Field(description="CSS class to apply to each option", alias="optionClass")] = (
        None
    )

    def in_locale(self, t: LocaleHandler) -> Self:
        self_copy = super().in_locale(t)
        return self_copy

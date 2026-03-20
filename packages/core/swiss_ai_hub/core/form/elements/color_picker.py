from typing import Annotated, Literal, Self

from pydantic import Field

from swiss_ai_hub.core.form.base.prime_vue_element import PrimeVueElement
from swiss_ai_hub.core.i18n.locale_handler import LocaleHandler


class ColorPicker(PrimeVueElement):
    """https://formkit-primevue.netlify.app/inputs/ColorPicker"""

    formkit: Annotated[Literal["primeColorPicker"], Field(description="PrimeVue ColorPicker element.")] = (
        "primeColorPicker"
    )
    disabled: Annotated[bool, Field(description="Whether the input is disabled")] = False
    readonly: Annotated[bool, Field(description="Whether the input is readonly")] = False
    inline: Annotated[bool, Field(description="Whether to display the picker inline")] = False
    format: Annotated[str | None, Field(description="Format of the color value (hex, rgb, hsl)")] = None

    def in_locale(self, t: LocaleHandler) -> Self:
        self_copy = super().in_locale(t)
        return self_copy

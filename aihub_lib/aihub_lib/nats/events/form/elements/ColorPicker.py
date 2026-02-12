from typing import Annotated, Literal, Self

from pydantic import Field

from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.nats.events.form.base.PrimeVueElement import PrimeVueElement


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

from typing import Annotated, Literal

from pydantic import Field

from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.nats.events.form.base.PrimeVueElement import PrimeVueElement


class Slider(PrimeVueElement):
    """https://formkit-primevue.netlify.app/inputs/Slider"""

    formkit: Annotated[Literal["primeSlider"], Field(description="PrimeVue Slider element.")] = "primeSlider"
    disabled: Annotated[bool, Field(description="Whether the input is disabled")] = False
    readonly: Annotated[bool, Field(description="Whether the input is readonly")] = False
    min: Annotated[float | None, Field(description="Minimum value")] = None
    max: Annotated[float | None, Field(description="Maximum value")] = None
    step: Annotated[float | None, Field(description="Step factor for increment/decrement")] = None
    range: Annotated[bool, Field(description="Whether to enable range selection")] = False
    orientation: Annotated[Literal["horizontal", "vertical"] | None, Field(description="Orientation of the slider")] = (
        None
    )

    def in_locale(self, t: LocaleHandler) -> "Slider":
        self_copy = super().in_locale(t)
        return self_copy

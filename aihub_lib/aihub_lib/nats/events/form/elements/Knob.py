from typing import Annotated, Literal

from pydantic import Field

from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.nats.events.form.base.PrimeVueElement import PrimeVueElement


class Knob(PrimeVueElement):
    """https://formkit-primevue.netlify.app/inputs/Knob"""

    formkit: Annotated[Literal["primeKnob"], Field(description="PrimeVue Knob element.")] = "primeKnob"
    disabled: Annotated[bool, Field(description="Whether the input is disabled")] = False
    readonly: Annotated[bool, Field(description="Whether the input is readonly")] = False
    min: Annotated[float | None, Field(description="Minimum value")] = None
    max: Annotated[float | None, Field(description="Maximum value")] = None
    step: Annotated[float | None, Field(description="Step factor for increment/decrement")] = None
    size: Annotated[int | None, Field(description="Size of the knob in pixels")] = None
    stroke_width: Annotated[int | None, Field(description="Width of the knob stroke", alias="strokeWidth")] = None
    show_value: Annotated[bool, Field(description="Whether to show the value in the center", alias="showValue")] = True
    value_color: Annotated[str | None, Field(description="Color of the value arc", alias="valueColor")] = None
    range_color: Annotated[str | None, Field(description="Color of the range arc", alias="rangeColor")] = None
    text_color: Annotated[str | None, Field(description="Color of the value text", alias="textColor")] = None
    value_template: Annotated[
        str | None, Field(description="Template string for value display", alias="valueTemplate")
    ] = None

    def in_locale(self, t: LocaleHandler) -> "Knob":
        self_copy = super().in_locale(t)
        return self_copy

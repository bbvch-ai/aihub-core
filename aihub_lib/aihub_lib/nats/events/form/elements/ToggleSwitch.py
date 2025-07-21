from typing import Annotated, Any, Literal

from pydantic import Field

from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events.form.base.PrimeVueElement import PrimeVueElement


class ToggleSwitch(PrimeVueElement):
    """https://formkit-primevue.netlify.app/inputs/ToggleSwitch"""

    formkit: Annotated[Literal["primeToggleSwitch"], Field(description="PrimeVue ToggleSwitch element.")] = (
        "primeToggleSwitch"
    )
    disabled: Annotated[bool, Field(description="Whether the input is disabled")] = False
    readonly: Annotated[bool, Field(description="Whether the input is readonly")] = False
    true_value: Annotated[Any, Field(description="Value to emit when toggled on", alias="trueValue")] = None
    false_value: Annotated[Any, Field(description="Value to emit when toggled off", alias="falseValue")] = None
    prefix: Annotated[LocaleString | str | None, Field(description="Prefix text")] = None
    suffix: Annotated[LocaleString | str | None, Field(description="Suffix text")] = None

    def in_locale(self, t: LocaleHandler) -> "ToggleSwitch":
        self_copy = super().in_locale(t)
        if isinstance(self_copy.prefix, LocaleString):
            self_copy.prefix = t.extract(self_copy.prefix)
        if isinstance(self_copy.suffix, LocaleString):
            self_copy.suffix = t.extract(self_copy.suffix)
        return self_copy

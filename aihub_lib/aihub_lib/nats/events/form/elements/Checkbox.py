from typing import Annotated, Literal, Self

from pydantic import Field

from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events.form.base.PrimeVueElement import PrimeVueElement

# Type for checkbox true/false values - typically bool, but can be str or int
CheckboxValue = bool | str | int | None


class Checkbox(PrimeVueElement):
    """https://formkit-primevue.netlify.app/inputs/Checkbox"""

    formkit: Annotated[Literal["primeCheckbox"], Field(description="PrimeVue Checkbox element.")] = "primeCheckbox"
    disabled: Annotated[bool, Field(description="Whether the input is disabled")] = False
    readonly: Annotated[bool, Field(description="Whether the input is readonly")] = False
    binary: Annotated[bool, Field(description="Whether the checkbox works in binary mode")] = True
    indeterminate: Annotated[bool, Field(description="Whether the checkbox is in indeterminate state")] = False
    true_value: Annotated[CheckboxValue, Field(description="Value to emit when checked", alias="trueValue")] = True
    false_value: Annotated[CheckboxValue, Field(description="Value to emit when unchecked", alias="falseValue")] = False
    prefix: Annotated[LocaleString | str | None, Field(description="Prefix text")] = None
    suffix: Annotated[LocaleString | str | None, Field(description="Suffix text")] = None

    def in_locale(self, t: LocaleHandler) -> Self:
        self_copy = super().in_locale(t)
        if isinstance(self_copy.prefix, LocaleString):
            self_copy.prefix = t.extract(self_copy.prefix)
        if isinstance(self_copy.suffix, LocaleString):
            self_copy.suffix = t.extract(self_copy.suffix)
        return self_copy

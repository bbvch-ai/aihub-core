from typing import Annotated, Literal, Self

from pydantic import Field, computed_field

from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.nats.events.form.base.PrimeVueElement import PrimeVueElement


class InputOtp(PrimeVueElement):
    """https://formkit-primevue.netlify.app/inputs/InputOtp"""

    formkit: Annotated[Literal["primeInputOtp"], Field(description="PrimeVue InputOtp element.")] = "primeInputOtp"
    disabled: Annotated[bool, Field(description="Whether the input is disabled")] = False
    readonly: Annotated[bool, Field(description="Whether the input is readonly")] = False
    length: Annotated[int, Field(description="Number of characters in the OTP")] = 4
    integer_only: Annotated[bool, Field(description="Whether to allow only integers", alias="integerOnly")] = False
    mask: Annotated[bool, Field(description="Whether to mask the input characters")] = False
    variant: Annotated[str | None, Field(description="Styling variant of the component")] = None

    @computed_field
    @property
    def validation(self) -> str:
        validation_rules = []
        base_validation = super().validation
        if base_validation:
            validation_rules.append(base_validation)

        validation_rules.append(f"length:{self.length}")

        if self.integer_only:
            validation_rules.append("matches:/^[0-9]+$/")

        return "|".join(validation_rules)

    def in_locale(self, t: LocaleHandler) -> Self:
        self_copy = super().in_locale(t)
        return self_copy

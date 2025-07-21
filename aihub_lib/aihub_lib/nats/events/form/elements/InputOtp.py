from typing import Annotated, Literal

from pydantic import Field

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

    def in_locale(self, t: LocaleHandler) -> "InputOtp":
        self_copy = super().in_locale(t)
        return self_copy
from typing import Annotated, Literal, Self

from pydantic import Field

from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events.form.base.PrimeVueElement import PrimeVueElement


class InputMask(PrimeVueElement):
    """https://formkit-primevue.netlify.app/inputs/InputMask"""

    formkit: Annotated[Literal["primeInputMask"], Field(description="PrimeVue InputMask element.")] = "primeInputMask"
    disabled: Annotated[bool, Field(description="Whether the input is disabled")] = False
    readonly: Annotated[bool, Field(description="Whether the input is readonly")] = False
    placeholder: Annotated[LocaleString | str | None, Field(description="Placeholder text")] = None
    mask: Annotated[str | None, Field(description="Input mask pattern")] = None
    slot_char: Annotated[str | None, Field(description="Placeholder character for mask slots", alias="slotChar")] = None
    auto_clear: Annotated[bool, Field(description="Whether to clear incomplete values on blur", alias="autoClear")] = (
        True
    )
    unmask: Annotated[bool, Field(description="Whether to return unmasked value")] = False
    icon_prefix: Annotated[
        str | None, Field(description="Icon prefix", alias="iconPrefix", pattern=r"^pi pi-[a-z0-9-]+$")
    ] = None
    icon_suffix: Annotated[
        str | None, Field(description="Icon suffix", alias="iconSuffix", pattern=r"^pi pi-[a-z0-9-]+$")
    ] = None

    def in_locale(self, t: LocaleHandler) -> Self:
        self_copy = super().in_locale(t)
        if isinstance(self_copy.placeholder, LocaleString):
            self_copy.placeholder = t.extract(self_copy.placeholder)
        return self_copy

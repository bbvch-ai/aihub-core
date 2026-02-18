from typing import Annotated, Literal

from pydantic import Field

from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events.form.base.PrimeVueElement import PrimeVueElement


class InputText(PrimeVueElement):
    """https://formkit-primevue.netlify.app/inputs/InputText"""

    formkit: Annotated[Literal["primeInputText"], Field(description="PrimeVue InputText element.")] = "primeInputText"
    disabled: Annotated[bool, Field(description="Whether the input is disabled")] = False
    readonly: Annotated[bool, Field(description="Whether the input is readonly")] = False
    placeholder: Annotated[LocaleString | str | None, Field(description="Placeholder text")] = None
    prefix: Annotated[LocaleString | str | None, Field(description="Prefix text")] = None
    suffix: Annotated[LocaleString | str | None, Field(description="Suffix text")] = None
    icon_prefix: Annotated[
        str | None, Field(description="Icon prefix", alias="iconPrefix", pattern=r"^pi pi-[a-z0-9-]+$")
    ] = None
    icon_suffix: Annotated[
        str | None, Field(description="Icon suffix", alias="iconSuffix", pattern=r"^pi pi-[a-z0-9-]+$")
    ] = None

    def in_locale(self, t: LocaleHandler) -> "PrimeVueElement":
        self_copy = super().in_locale(t)
        if isinstance(self_copy.placeholder, LocaleString):
            self_copy.placeholder = t.extract(self_copy.placeholder)
        if isinstance(self_copy.prefix, LocaleString):
            self_copy.prefix = t.extract(self_copy.prefix)
        if isinstance(self_copy.suffix, LocaleString):
            self_copy.suffix = t.extract(self_copy.suffix)
        return self_copy

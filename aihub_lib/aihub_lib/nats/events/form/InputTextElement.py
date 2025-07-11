from typing import Annotated, Literal

from pydantic import Field

from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events.form.base.PrimeVueElement import PrimeVueElement


class InputTextElement(PrimeVueElement):
    formkit: Annotated[Literal["primeInputText"], Field(description="PrimeVue InputText element.")] = "primeInputText"
    disabled: Annotated[bool, Field(description="Whether the input is disabled")] = False
    readonly: Annotated[bool, Field(description="Whether the input is disabled")] = False
    placeholder: Annotated[LocaleString | None, Field(description="Placeholder text")] = None
    prefix: Annotated[LocaleString | None, Field(description="Prefix text")] = None
    suffix: Annotated[LocaleString | None, Field(description="Suffix text")] = None
    icon_prefix: Annotated[str | None, Field(description="Icon prefix", alias="iconPrefix", pattern=r"^pi pi-[a-z0-9-]+$")] = None
    icon_suffix: Annotated[str | None, Field(description="Icon suffix", alias="iconSuffix", pattern=r"^pi pi-[a-z0-9-]+$")] = None

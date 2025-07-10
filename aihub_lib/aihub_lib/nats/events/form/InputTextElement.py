from typing import Annotated, Literal

from pydantic import Field

from aihub_lib.nats.events.form.base.PrimeVueElement import PrimeVueElement


class InputTextElement(PrimeVueElement):
    formkit: Annotated[Literal["primeInputText"], Field(description="PrimeVue InputText element.")] = "primeInputText"
    disabled: Annotated[bool, Field(description="Whether the input is disabled")] = False
    readonly: Annotated[bool, Field(description="Whether the input is disabled")] = False
    placeholder: Annotated[str, Field(description="Placeholder text")] = ""
    prefix: Annotated[str, Field(description="Prefix text")] = ""
    suffix: Annotated[str, Field(description="Suffix text")] = ""
    icon_prefix: Annotated[str, Field(description="Icon prefix", alias="iconPrefix", pattern=r"^pi pi-[a-z0-9-]+$")] = (
        ""
    )
    icon_suffix: Annotated[str, Field(description="Icon suffix", alias="iconSuffix", pattern=r"^pi pi-[a-z0-9-]+$")] = (
        ""
    )

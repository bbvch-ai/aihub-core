from typing import Annotated, Literal, Self

from pydantic import Field

from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events.form.base.PrimeVueElement import PrimeVueElement


class ToggleButton(PrimeVueElement):
    """https://formkit-primevue.netlify.app/inputs/ToggleButton"""

    formkit: Annotated[Literal["primeToggleButton"], Field(description="PrimeVue ToggleButton element.")] = (
        "primeToggleButton"
    )
    disabled: Annotated[bool, Field(description="Whether the input is disabled")] = False
    readonly: Annotated[bool, Field(description="Whether the input is readonly")] = False
    on_label: Annotated[LocaleString | str | None, Field(description="Label for the on state", alias="onLabel")] = None
    off_label: Annotated[LocaleString | str | None, Field(description="Label for the off state", alias="offLabel")] = (
        None
    )
    on_icon: Annotated[
        str | None, Field(description="Icon for the on state", alias="onIcon", pattern=r"^pi pi-[a-z0-9-]+$")
    ] = None
    off_icon: Annotated[
        str | None, Field(description="Icon for the off state", alias="offIcon", pattern=r"^pi pi-[a-z0-9-]+$")
    ] = None
    icon_pos: Annotated[Literal["left", "right"] | None, Field(description="Position of the icon", alias="iconPos")] = (
        None
    )

    def in_locale(self, t: LocaleHandler) -> Self:
        self_copy = super().in_locale(t)
        if isinstance(self_copy.on_label, LocaleString):
            self_copy.on_label = t.extract(self_copy.on_label)
        if isinstance(self_copy.off_label, LocaleString):
            self_copy.off_label = t.extract(self_copy.off_label)
        return self_copy

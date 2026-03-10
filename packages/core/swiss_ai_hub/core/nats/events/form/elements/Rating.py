from typing import Annotated, Literal, Self

from pydantic import Field, computed_field

from swiss_ai_hub.core.i18n.LocaleHandler import LocaleHandler
from swiss_ai_hub.core.nats.events.form.base.PrimeVueElement import PrimeVueElement


class Rating(PrimeVueElement):
    """https://formkit-primevue.netlify.app/inputs/Rating"""

    formkit: Annotated[Literal["primeRating"], Field(description="PrimeVue Rating element.")] = "primeRating"
    disabled: Annotated[bool, Field(description="Whether the input is disabled")] = False
    readonly: Annotated[bool, Field(description="Whether the input is readonly")] = False
    stars: Annotated[int, Field(description="Number of stars to display")] = 5
    cancel: Annotated[bool, Field(description="Whether to show cancel button to clear rating")] = False
    on_icon: Annotated[
        str | None, Field(description="Icon for selected state", alias="onIcon", pattern=r"^pi pi-[a-z0-9-]+$")
    ] = None
    off_icon: Annotated[
        str | None, Field(description="Icon for unselected state", alias="offIcon", pattern=r"^pi pi-[a-z0-9-]+$")
    ] = None
    cancel_icon: Annotated[
        str | None, Field(description="Icon for cancel button", alias="cancelIcon", pattern=r"^pi pi-[a-z0-9-]+$")
    ] = None

    @computed_field
    @property
    def validation(self) -> str:
        validation_rules = []
        base_validation = super().validation
        if base_validation:
            validation_rules.append(base_validation)

        validation_rules.append("integer")

        min_value = 0 if self.cancel else 1
        validation_rules.append(f"min:{min_value}")

        validation_rules.append(f"max:{self.stars}")

        return "|".join(validation_rules)

    def in_locale(self, t: LocaleHandler) -> Self:
        self_copy = super().in_locale(t)
        return self_copy

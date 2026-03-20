from typing import Annotated, Literal, Self

from pydantic import Field, computed_field

from swiss_ai_hub.core.form.base.prime_vue_element import PrimeVueElement
from swiss_ai_hub.core.i18n.locale_handler import LocaleHandler


class Slider(PrimeVueElement):
    """https://formkit-primevue.netlify.app/inputs/Slider"""

    formkit: Annotated[Literal["primeSlider"], Field(description="PrimeVue Slider element.")] = "primeSlider"
    disabled: Annotated[bool, Field(description="Whether the input is disabled")] = False
    readonly: Annotated[bool, Field(description="Whether the input is readonly")] = False
    min: Annotated[float | None, Field(description="Minimum value")] = None
    max: Annotated[float | None, Field(description="Maximum value")] = None
    step: Annotated[float | None, Field(description="Step factor for increment/decrement")] = None
    range: Annotated[bool, Field(description="Whether to enable range selection")] = False
    orientation: Annotated[Literal["horizontal", "vertical"] | None, Field(description="Orientation of the slider")] = (
        None
    )

    @computed_field
    @property
    def validation(self) -> str:
        validation_rules = []
        base_validation = super().validation
        if base_validation:
            validation_rules.append(base_validation)

        validation_rules.append("number")

        if self.min is not None:
            validation_rules.append(f"min:{self.min}")

        if self.max is not None:
            validation_rules.append(f"max:{self.max}")

        return "|".join(validation_rules)

    def in_locale(self, t: LocaleHandler) -> Self:
        self_copy = super().in_locale(t)
        return self_copy

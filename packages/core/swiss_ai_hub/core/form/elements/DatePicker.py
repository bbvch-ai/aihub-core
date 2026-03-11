from typing import Annotated, Literal, Self

from pydantic import Field, computed_field

from swiss_ai_hub.core.form.base.PrimeVueElement import PrimeVueElement
from swiss_ai_hub.core.i18n.LocaleHandler import LocaleHandler
from swiss_ai_hub.core.i18n.LocaleString import LocaleString


class DatePicker(PrimeVueElement):
    """https://formkit-primevue.netlify.app/inputs/DatePicker"""

    formkit: Annotated[Literal["primeDatePicker"], Field(description="PrimeVue DatePicker element.")] = (
        "primeDatePicker"
    )
    disabled: Annotated[bool, Field(description="Whether the input is disabled")] = False
    readonly: Annotated[bool, Field(description="Whether the input is readonly")] = False
    placeholder: Annotated[LocaleString | str | None, Field(description="Placeholder text")] = None
    date_format: Annotated[str | None, Field(description="Format of the date display", alias="dateFormat")] = "dd.mm.yy"
    show_icon: Annotated[bool, Field(description="Whether to show the calendar icon", alias="showIcon")] = False
    icon: Annotated[str | None, Field(description="Custom icon class", pattern=r"^pi pi-[a-z0-9-]+$")] = None
    selection_mode: Annotated[
        Literal["single", "range", "multiple"], Field(description="Selection mode for dates", alias="selectionMode")
    ] = "single"
    manual_input: Annotated[bool, Field(description="Whether to allow manual input", alias="manualInput")] = True

    @computed_field
    @property
    def validation(self) -> str:
        validation_rules = []
        base_validation = super().validation
        if base_validation:
            validation_rules.append(base_validation)

        validation_rules.append("date")

        return "|".join(validation_rules)

    def in_locale(self, t: LocaleHandler) -> Self:
        self_copy = super().in_locale(t)
        if isinstance(self_copy.placeholder, LocaleString):
            self_copy.placeholder = t.extract(self_copy.placeholder)
        return self_copy

from decimal import Decimal
from typing import Annotated, Literal, Self

from pydantic import Field, computed_field, model_validator

from swiss_ai_hub.core.form.base.prime_vue_element import PrimeVueElement
from swiss_ai_hub.core.i18n.locale_handler import LocaleHandler
from swiss_ai_hub.core.i18n.locale_string import LocaleString


class InputNumber(PrimeVueElement):
    """https://formkit-primevue.netlify.app/inputs/InputNumber"""

    formkit: Annotated[Literal["primeInputNumber"], Field(description="PrimeVue InputNumber element.")] = (
        "primeInputNumber"
    )
    disabled: Annotated[bool, Field(description="Whether the input is disabled")] = False
    readonly: Annotated[bool, Field(description="Whether the input is readonly")] = False
    placeholder: Annotated[LocaleString | str | None, Field(description="Placeholder text")] = None
    min: Annotated[float | None, Field(description="Minimum value")] = None
    max: Annotated[float | None, Field(description="Maximum value")] = None
    step: Annotated[float | None, Field(description="Step factor for increment/decrement")] = None
    use_grouping: Annotated[bool, Field(description="Whether to use grouping separators", alias="useGrouping")] = True
    min_fraction_digits: Annotated[
        int | None, Field(description="Minimum number of fraction digits", alias="minFractionDigits")
    ] = None
    max_fraction_digits: Annotated[
        int | None, Field(description="Maximum number of fraction digits", alias="maxFractionDigits")
    ] = None
    locale: Annotated[str | None, Field(description="Locale to use for number formatting")] = None
    mode: Annotated[Literal["decimal", "currency"] | None, Field(description="Input mode")] = None
    currency: Annotated[str | None, Field(description="Currency code for currency mode")] = None
    prefix: Annotated[LocaleString | str | None, Field(description="Prefix text")] = None
    suffix: Annotated[LocaleString | str | None, Field(description="Suffix text")] = None
    show_buttons: Annotated[
        bool, Field(description="Whether to show increment/decrement buttons", alias="showButtons")
    ] = False
    button_layout: Annotated[
        Literal["stacked", "horizontal"] | None,
        Field(description="Layout of increment/decrement buttons", alias="buttonLayout"),
    ] = None

    @model_validator(mode="after")
    def _allow_fractional_input(self) -> Self:
        # PrimeVue InputNumber is integer-only unless fraction digits are configured, so a
        # fractional field (e.g. temperature with step 0.1) would reject the decimal point.
        # When unset, allow as many fraction digits as the field's own precision implies.
        if self.max_fraction_digits is None:
            numeric = [value for value in (self.step, self.min, self.max, self.value) if isinstance(value, float)]
            decimals = max((self._decimal_places(value) for value in numeric), default=0)
            if decimals:
                self.max_fraction_digits = decimals
                if self.min_fraction_digits is None:
                    self.min_fraction_digits = 0
        return self

    @staticmethod
    def _decimal_places(value: float) -> int:
        exponent = Decimal(repr(value)).normalize().as_tuple().exponent
        return -exponent if isinstance(exponent, int) and exponent < 0 else 0

    @computed_field
    @property
    def validation(self) -> str:
        validation_rules = []
        base_validation = super().validation
        if base_validation:
            validation_rules.append(base_validation)

        validation_rules.append("number")

        if self.min is not None:
            validation_rules.append(f"min:{self._format_bound(self.min)}")

        if self.max is not None:
            validation_rules.append(f"max:{self._format_bound(self.max)}")

        return "|".join(validation_rules)

    @staticmethod
    def _format_bound(value: float) -> str:
        # FormKit's min/max rules can't parse scientific notation like "1e-07" or "1e+06".
        # `repr(float)` is the shortest exact-roundtrip string (no precision artefacts), and
        # `Decimal` formatted with `f` expands any scientific form into plain decimals at
        # any magnitude. Trailing zeros and a dangling `.` are stripped so 5.0 → "5".
        return format(Decimal(repr(value)), "f").rstrip("0").rstrip(".")

    def in_locale(self, t: LocaleHandler) -> Self:
        self_copy = super().in_locale(t)
        if isinstance(self_copy.placeholder, LocaleString):
            self_copy.placeholder = t.extract(self_copy.placeholder)
        if isinstance(self_copy.prefix, LocaleString):
            self_copy.prefix = t.extract(self_copy.prefix)
        if isinstance(self_copy.suffix, LocaleString):
            self_copy.suffix = t.extract(self_copy.suffix)
        return self_copy

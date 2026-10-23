from typing import Annotated, Any, Literal, Self

from pydantic import Field, computed_field

from swiss_ai_hub.core.form.base.prime_vue_element import PrimeVueElement
from swiss_ai_hub.core.i18n.locale_handler import LocaleHandler
from swiss_ai_hub.core.i18n.locale_string import LocaleString


class Textarea(PrimeVueElement):
    """https://formkit-primevue.netlify.app/inputs/Textarea"""

    formkit: Annotated[Literal["primeTextarea"], Field(description="PrimeVue Textarea element.")] = "primeTextarea"
    disabled: Annotated[bool, Field(description="Whether the input is disabled")] = False
    readonly: Annotated[bool, Field(description="Whether the input is readonly")] = False
    placeholder: Annotated[LocaleString | str | None, Field(description="Placeholder text")] = None
    rows: Annotated[int | None, Field(description="Number of rows to display")] = None
    auto_resize: Annotated[
        bool, Field(description="Whether to automatically resize based on content", alias="autoResize")
    ] = False
    max_length: Annotated[int | None, Field(description="Maximum number of characters", alias="maxlength", ge=1)] = None

    @computed_field
    @property
    def validation(self) -> str:
        rules = []
        base_validation = super().validation
        if base_validation:
            rules.append(base_validation)
        if self.max_length is not None:
            rules.append(f"length:0,{self.max_length}")
        return "|".join(rules)

    def validate_value(self, field_path: str, value: Any, t: LocaleHandler) -> list[str]:
        """Enforces `max_length` on save, since `maxlength` only stops typing in the browser."""
        if self.max_length is not None and isinstance(value, str) and len(value) > self.max_length:
            return [f"must be at most {self.max_length} characters"]
        return []

    def in_locale(self, t: LocaleHandler) -> Self:
        self_copy = super().in_locale(t)
        if isinstance(self_copy.placeholder, LocaleString):
            self_copy.placeholder = t.extract(self_copy.placeholder)
        return self_copy

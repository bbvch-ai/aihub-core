from typing import Annotated, Literal, Self

from pydantic import Field

from swiss_ai_hub.core.form.base.PrimeVueElement import PrimeVueElement
from swiss_ai_hub.core.i18n.LocaleHandler import LocaleHandler
from swiss_ai_hub.core.i18n.LocaleString import LocaleString


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

    def in_locale(self, t: LocaleHandler) -> Self:
        self_copy = super().in_locale(t)
        if isinstance(self_copy.placeholder, LocaleString):
            self_copy.placeholder = t.extract(self_copy.placeholder)
        return self_copy

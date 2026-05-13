from typing import Annotated, Literal, Self

from pydantic import Field

from swiss_ai_hub.core.form.base.prime_vue_element import PrimeVueElement
from swiss_ai_hub.core.i18n.locale_handler import LocaleHandler
from swiss_ai_hub.core.i18n.locale_string import LocaleString


class ChipsInput(PrimeVueElement):
    """FormKit element for free-text list[str] entry (renders as PrimeVue AutoComplete with chips)."""

    formkit: Annotated[Literal["chipsInput"], Field(description="Chips input element.")] = "chipsInput"
    placeholder: Annotated[LocaleString | str | None, Field(description="Input placeholder.")] = None

    def in_locale(self, t: LocaleHandler) -> Self:
        self_copy = super().in_locale(t)
        if isinstance(self_copy.placeholder, LocaleString):
            self_copy.placeholder = t.extract(self_copy.placeholder)
        return self_copy

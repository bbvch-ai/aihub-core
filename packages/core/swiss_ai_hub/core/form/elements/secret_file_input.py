from typing import Annotated, Literal, Self

from pydantic import Field

from swiss_ai_hub.core.form.base.prime_vue_element import PrimeVueElement
from swiss_ai_hub.core.i18n.locale_handler import LocaleHandler
from swiss_ai_hub.core.i18n.locale_string import LocaleString


class SecretFileInput(PrimeVueElement):
    """
    A secret that is handed out as a file, such as a service-account key, picked instead of pasted.

    The browser reads the file and submits its text contents, so the value is an ordinary string: it is
    encrypted, masked and restored exactly like a ``Password`` value, and API clients keep sending a string.
    """

    formkit: Annotated[Literal["secretFileInput"], Field(description="Secret file input element.")] = "secretFileInput"
    accept: Annotated[str | None, Field(description="File types the picker offers, e.g. '.json'")] = None
    max_size_bytes: Annotated[
        int, Field(description="Largest file accepted, checked before it is read", alias="maxSizeBytes")
    ] = 65536
    placeholder: Annotated[LocaleString | str | None, Field(description="Placeholder text")] = None

    def in_locale(self, t: LocaleHandler) -> Self:
        self_copy = super().in_locale(t)
        if isinstance(self_copy.placeholder, LocaleString):
            self_copy.placeholder = t.extract(self_copy.placeholder)
        return self_copy

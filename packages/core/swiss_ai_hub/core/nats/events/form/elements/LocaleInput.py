from typing import Annotated, Literal, Self

from pydantic import Field

from swiss_ai_hub.core.i18n.LocaleHandler import LocaleHandler
from swiss_ai_hub.core.i18n.LocaleString import LocaleString
from swiss_ai_hub.core.nats.events.form.base.PrimeVueElement import PrimeVueElement


class LocaleInput(PrimeVueElement):
    """
    A FormKit element for entering multi-language text (LocaleString values).

    This element renders as a text input with language switching capability,
    allowing users to enter translations for all supported languages (de, en, fr, it)
    in a single compact UI component.

    The frontend renders this as an input field with a language selector, where users
    can switch between languages to enter the corresponding translation.

    ### Form Duality
    When used in a Form, this element captures a LocaleString value with translations
    for each language. The form submission returns a dict with language keys.

    ### Example Usage
    ```python
    class MyAgentConfig(AgentConfig):
        custom_greeting: Annotated[
            LocaleString | LocaleInput,
            Field(description="Custom greeting message"),
        ]

    # Form mode - for rendering:
    config = MyAgentConfig(
        ...,
        custom_greeting=LocaleInput(label=LocaleString(en="Greeting", de="Begrüßung")),
    )

    # Data mode - from submission:
    config = MyAgentConfig(
        ...,
        custom_greeting=LocaleString(en="Hello", de="Hallo", fr="Bonjour", it="Ciao"),
    )
    ```
    """

    formkit: Annotated[Literal["localeInput"], Field(description="Locale input element.")] = "localeInput"

    input_type: Annotated[
        Literal["text", "textarea"],
        Field(description="Input type: 'text' for single-line, 'textarea' for multi-line", alias="inputType"),
    ] = "text"

    rows: Annotated[
        int,
        Field(description="Number of rows for textarea mode (ignored for text mode)"),
    ] = 3

    placeholder: Annotated[LocaleString | str | None, Field(description="Placeholder text for each language")] = None

    def in_locale(self, t: LocaleHandler) -> Self:
        self_copy = super().in_locale(t)
        if isinstance(self_copy.placeholder, LocaleString):
            self_copy.placeholder = t.extract(self_copy.placeholder)
        return self_copy

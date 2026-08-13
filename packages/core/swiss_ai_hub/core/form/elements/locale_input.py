from typing import Annotated, Literal, Self

from pydantic import Field, computed_field

from swiss_ai_hub.core.form.base.prime_vue_element import PrimeVueElement
from swiss_ai_hub.core.i18n.locale_handler import LocaleHandler
from swiss_ai_hub.core.i18n.locale_string import LocaleString


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

    @computed_field
    @property
    def validation(self) -> str:
        """Emits `localeRequired` where other elements emit FormKit's `required`.

        FormKit's `required` rule only asks whether a value is present, and this element's
        value is always a `{de, en, fr, it}` object — non-empty, therefore passing, even when
        every locale inside it is blank. `localeRequired` (registered in the frontend FormKit
        config) looks at the locale values themselves.
        """
        rules: list[str] = []
        if self.required:
            rules.append("localeRequired")
        if self.additional_validation_rules:
            rules.append(self.additional_validation_rules)
        return "|".join(rules)

    def in_locale(self, t: LocaleHandler) -> Self:
        self_copy = super().in_locale(t)
        if isinstance(self_copy.placeholder, LocaleString):
            self_copy.placeholder = t.extract(self_copy.placeholder)
        return self_copy

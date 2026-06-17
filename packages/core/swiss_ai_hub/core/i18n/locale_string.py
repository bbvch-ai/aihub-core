from __future__ import annotations

from typing import TYPE_CHECKING, Annotated, Literal

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from swiss_ai_hub.core.form.elements.locale_input import LocaleInput


class LocaleString(BaseModel):
    """
    A multi-language string container supporting German, English, French, and Italian.

    LocaleString serves as a data container for translated strings. For form rendering,
    use the `LocaleInput` FormKit element with the duality pattern.

    ## Basic Usage (Data Mode)

    ```python
    greeting = LocaleString(
        de="Hallo",
        en="Hello",
        fr="Bonjour",
        it="Ciao",
    )
    print(greeting.in_locale("en"))  # "Hello"
    ```

    ## Form Duality Pattern

    For form fields that accept LocaleString values, use the union type pattern:

    ```python
    class MyConfig(Form):
        name: Annotated[LocaleString | LocaleInput, Field(description="Name")]

    # Form mode - for rendering:
    config = MyConfig(name=LocaleInput(label=LocaleString(en="Name", de="Name")))

    # Data mode - from submission:
    config = MyConfig(name=LocaleString(en="Hello", de="Hallo", fr="Bonjour", it="Ciao"))
    ```

    For convenience, use `LocaleString.as_form()` to create a pre-configured `LocaleInput`:

    ```python
    config = MyConfig(name=LocaleString.as_form(label=LocaleString(en="Name", de="Name")))
    ```
    """

    de: Annotated[str | None, Field(description="German")] = None
    en: Annotated[str | None, Field(description="English")] = None
    fr: Annotated[str | None, Field(description="French")] = None
    it: Annotated[str | None, Field(description="Italian")] = None

    def in_locale(self, locale: str, fallback: bool = True) -> str | None:
        """Extract the string for a locale, falling back to other locales if it is unset.

        With `fallback` (the default), mirrors `LocaleHandler.extract_multi_locale`:
        requested locale → default locale → first populated locale in the whitelist;
        unlike that method it returns None instead of raising when every locale is empty.

        Pass `fallback=False` to read exactly the requested locale (no substitution) — for
        callers that need the requested language verbatim or want their own fallback order.
        """
        value = getattr(self, locale, None)
        if value or not fallback:
            return value

        from swiss_ai_hub.core.i18n.locale_handler import LocaleHandler

        for field in (LocaleHandler.DEFAULT_LOCALE, *LocaleHandler.LOCALE_WHITE_LIST):
            if fallback_value := getattr(self, field, None):
                return fallback_value
        return None

    @classmethod
    def from_i18n_path(cls, path: str) -> LocaleString:
        """Create a LocaleString from an i18n translation path.

        The path format is `{scope}.{filename}.{path}` where translations are loaded
        from `{scope}/{filename}.{locale}.yml` files. All translation directories
        across the monorepo (lib, api, agent, process, bot) are automatically discovered.
        """
        from swiss_ai_hub.core.i18n.locale_handler import LocaleHandler

        return cls(
            de=LocaleHandler("de")(path),
            en=LocaleHandler("en")(path),
            fr=LocaleHandler("fr")(path),
            it=LocaleHandler("it")(path),
        )

    @classmethod
    def as_form(
        cls,
        label: LocaleString | None = None,
        input_type: Literal["text", "textarea"] = "text",
        rows: int = 3,
        help_text: LocaleString | None = None,
        condition_if: str | None = None,
    ) -> LocaleInput:
        """
        Factory method to create a LocaleInput element for form rendering.

        Use this to create a form input element that captures multi-language string
        values. The returned LocaleInput element renders as a text input with
        language switching capability in the frontend.
        """
        from swiss_ai_hub.core.form.elements.locale_input import LocaleInput

        return LocaleInput(
            label=label or LocaleString(en="Value", de="Wert", fr="Valeur", it="Valore"),
            input_type=input_type,
            rows=rows,
            help=help_text,
            condition_if=condition_if,
        )

    def _has_form_elements(self) -> bool:
        """
        Check if any field contains a FormkitElement.

        Deprecated: LocaleString no longer stores FormkitElements. Use LocaleInput
        with the duality pattern instead. This method is kept for backwards
        compatibility and always returns False.
        """
        return False

    def _to_formkit_elements(self) -> list:
        """
        Extract FormkitElement instances from language fields.

        Deprecated: LocaleString no longer stores FormkitElements. Use LocaleInput
        with the duality pattern instead. This method is kept for backwards
        compatibility and always returns an empty list.
        """
        return []

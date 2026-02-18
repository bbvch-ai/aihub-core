import abc
from typing import Annotated, Self

from pydantic import Field, computed_field

from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events.form.base.FormkitElement import FormkitElement

# Type alias for form field values - covers all realistic form data types
# Avoids 'Any' which generates schema without type (breaks jambo)
FormValue = str | int | float | bool | list[str] | dict[str, str] | None


class PrimeVueElement(FormkitElement, abc.ABC):
    """
    https://sfxcode.github.io/formkit-primevue/guide/
    Class to generate an form input using primevue elements. We use an external library that extends the default
    components from formkit using primevue elements, and for each of these elements, a subclass of this class
    is available that lets you create InputText, CheckBoxes etc.
    """

    formkit: Annotated[str, Field(description="Primevue Element", alias="$formkit")]
    name: Annotated[str | None, Field(description="Name of this field")] = None
    label: Annotated[LocaleString | str, Field(description="Label of this field")]
    help: Annotated[LocaleString | str | None, Field(description="Help text of this field")] = None
    value: Annotated[FormValue, Field(description="Default value for this field")] = None

    required: Annotated[bool, Field(description="Whether this field is required")] = False

    # https://formkit.com/essentials/validation
    additional_validation_rules: Annotated[str | None, Field(description="Validation expression")] = None

    @computed_field
    @property
    def validation(self) -> str:
        rules: list[str] = []
        if self.required:
            rules.append("required")
        if self.additional_validation_rules:
            rules.append(self.additional_validation_rules)
        return "|".join(rules)

    def in_locale(self, t: LocaleHandler) -> Self:
        self_copy = self.model_copy()
        if isinstance(self_copy.label, LocaleString):
            self_copy.label = t.extract(self_copy.label)
        if isinstance(self_copy.help, LocaleString):
            self_copy.help = t.extract(self_copy.help)
        if "required" in self_copy.validation and "*" not in self_copy.label:
            self_copy.label = f"{self_copy.label} *"
        return self_copy

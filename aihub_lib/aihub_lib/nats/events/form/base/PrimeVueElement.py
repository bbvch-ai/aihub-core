import abc
from typing import Annotated

from pydantic import Field

from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events.form.base.FormkitElement import FormkitElement


class PrimeVueElement(FormkitElement, abc.ABC):
    """
    https://sfxcode.github.io/formkit-primevue/guide/
    Class to generate an form input using primevue elements. We use an external library that extends the default
    components from formkit using primevue elements, and for each of these elements, a subclass of this class
    is available that lets you create InputText, CheckBoxes etc.
    """

    formkit: Annotated[str, Field(description="Primevue Element")]
    name: Annotated[str | None, Field(description="Name of this field")] = None
    label: Annotated[LocaleString, Field(description="Label of this field")]
    help: Annotated[LocaleString | None, Field(description="Help text of this field")] = None

    # https://formkit.com/essentials/validation
    validation: Annotated[str | None, Field(description="Validation expression")] = None

    def in_locale(self, t: LocaleHandler) -> "PrimeVueElement":
        self_copy = self.model_copy()
        if isinstance(self_copy.label, LocaleString):
            self_copy.label = t.extract(self_copy.label)
        if isinstance(self_copy.help, LocaleString):
            self_copy.help = t.extract(self_copy.help)
        return self_copy

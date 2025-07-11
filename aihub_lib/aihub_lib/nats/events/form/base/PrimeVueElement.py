import abc
from typing import Annotated

from pydantic import Field

from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events.form.base.FormkitElement import FormkitElement


class PrimeVueElement(FormkitElement, abc.ABC):
    formkit: Annotated[str, Field(description="Primevue Element")]
    name: Annotated[str | None, Field(description="Name of this field")] = None
    label: Annotated[LocaleString, Field(description="Label of this field")]
    help: Annotated[LocaleString | None, Field(description="Help text of this field")] = None
    # https://formkit.com/essentials/validation
    validation: Annotated[str | None, Field(description="Validation expression")] = None

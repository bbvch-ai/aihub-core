import abc
from typing import Annotated

from pydantic import Field

from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events.work_request.human.form.base.FormkitElement import FormkitElement


class PrimeVueElement(FormkitElement, abc.ABC):
    formkit: Annotated[str, Field(description="Primevue Element")]
    label: Annotated[str | LocaleString, Field(description="Label of this field")]
    help: Annotated[str | LocaleString | None, Field(description="Help text of this field")] = None
    # https://formkit.com/essentials/validation
    validation: Annotated[str | None, Field(description="Validation expression")] = None

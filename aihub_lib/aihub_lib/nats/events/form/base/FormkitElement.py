import abc
from typing import Annotated, Literal

from openai import BaseModel
from pydantic import Field, ConfigDict

from aihub_lib.i18n.LocaleHandler import LocaleHandler


class FormkitElement(BaseModel, abc.ABC):
    model_config = ConfigDict(populate_by_name=True)

    is_formkit_element: Annotated[Literal[True], Field(description="Indicates that this element is a FormKit element")] = True
    condition_if: Annotated[
        str | None, Field(description="Conditional expression to show this element", alias="if", pattern=r"^\$.+")
    ] = None

    @abc.abstractmethod
    def in_locale(self, t: LocaleHandler) -> "FormkitElement":
        ...
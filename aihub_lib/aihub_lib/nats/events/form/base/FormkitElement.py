import abc
from typing import Annotated, Literal, Self

from openai import BaseModel
from pydantic import ConfigDict, Field

from aihub_lib.i18n.LocaleHandler import LocaleHandler


class FormkitElement(BaseModel, abc.ABC):
    """
    https://formkit.com/essentials/schema
    Base class for all formkit elements. Instances of these formkit elements will be recognized when placed on
    a Form-model and be converted into data structures that formkit can render in the frontend.
    """

    model_config = ConfigDict(populate_by_name=True)

    is_formkit_element: Annotated[
        Literal[True], Field(description="Indicates that this element is a FormKit element")
    ] = True
    condition_if: Annotated[
        str | None, Field(description="Conditional expression to show this element", alias="if", pattern=r"^\$.+")
    ] = None
    ref: Annotated[str | None, Field(description="Unique identifier for this element", alias="id")] = None

    @abc.abstractmethod
    def in_locale(self, t: LocaleHandler) -> Self: ...

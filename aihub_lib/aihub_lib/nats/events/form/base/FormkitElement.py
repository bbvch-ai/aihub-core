from typing import Annotated, Literal

from openai import BaseModel
from pydantic import Field


class FormkitElement(BaseModel):
    is_formkit_element: Annotated[Literal[True], Field(description="Indicates that this element is a FormKit element")] = True
    condition_if: Annotated[
        str | None, Field(description="Conditional expression to show this element", alias="if", pattern=r"^\$.+")
    ] = None

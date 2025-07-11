from typing import Annotated

from openai import BaseModel
from pydantic import Field


class FormkitElement(BaseModel):
    condition_if: Annotated[
        str | None, Field(description="Conditional expression to show this element", alias="if", pattern=r"^\$.+")
    ] = None

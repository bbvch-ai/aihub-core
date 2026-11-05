from typing import Annotated

from pydantic import BaseModel, Field


class ExtractionFormPart(BaseModel):
    """One part of an extraction request as the request form asks it back: what was understood, whether the request
    named it, whether its second option drops it, and the hint with examples the dialog's answer field cannot show."""

    key: Annotated[str, Field(description="The question id and i18n key: where, rows, columns, exact or semantic.")]
    value: Annotated[str, Field(description="The part as understood, or what applies when the request named none.")]
    named: Annotated[bool, Field(description="Whether the request named this part.")]
    droppable: Annotated[bool, Field(description="Whether a second option drops the part (anything, none).")]
    hint: Annotated[str, Field(description="What the part may say, with examples.")]

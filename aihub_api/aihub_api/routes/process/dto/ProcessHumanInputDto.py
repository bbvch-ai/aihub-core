from typing import Annotated

from aihub_lib.nats.events.form import ALL_FORM_OPTIONS
from pydantic import BaseModel, Field


class ProcessHumanInputDto(BaseModel):
    """
    Defines what and how a piece of work must be submitted by a user to a process.
    As humans usually submit their data by filling in forms in the frontend, this event holds
    a list of formkit form fields that can be used to generate a formkit form in the frontend.
    Submitting the form will lead to the required data structure that can be submitted
    to the <route> using the http-method <method>.
    """

    name: Annotated[str, Field(description="The name of the work event.")]
    description: Annotated[
        str, Field(description="A description of the work event, providing details about its purpose.")
    ]
    route: Annotated[str, Field(description="The route of the work event.")]
    method: Annotated[str, Field(description="The HTTP method of the work event.")]
    form: Annotated[list[ALL_FORM_OPTIONS], Field(description="Formkit fields to render the UI")]

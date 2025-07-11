from typing import Annotated

from pydantic import BaseModel, Field

from aihub_lib.nats.events.form import ALL_FORM_OPTIONS


class ProcessStartDTO(BaseModel):
    route: Annotated[str, Field(description="The route of the work event.")]
    method: Annotated[str, Field(description="The HTTP method of the work event.")]
    form: Annotated[list[ALL_FORM_OPTIONS], Field(description="Formkit fields to render the UI")]
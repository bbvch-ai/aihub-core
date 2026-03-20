from typing import Annotated

from pydantic import BaseModel, Field

from swiss_ai_hub.core.events.discovery.event_specs import EventSpecs
from swiss_ai_hub.core.form import ALL_FORM_OPTIONS
from swiss_ai_hub.core.i18n.locale_string import LocaleString


class HumanInSpecs(BaseModel):
    """
    Defines a piece of work that can be submitted by a human.
    It holds information about the form that the user must fill in in order to generate the exact
    data structure defined in the event specs of the work event.
    It also holds the route and http method that must be used to finally post that work event data
    to the API, which will forward it to the appropriate process.
    """

    name: Annotated[LocaleString, Field(description="The name of the work event.")]
    description: Annotated[
        LocaleString, Field(description="A description of the work event, providing details about its purpose.")
    ]
    route: Annotated[str, Field(description="The route of the work event.")]
    method: Annotated[str, Field(description="The HTTP method of the work event.")]
    is_process_start: Annotated[bool, Field(description="Whether the work event is a process start event.")]
    event_specs: Annotated[EventSpecs, Field(description="The event specs of the work event.")]
    form: Annotated[list[ALL_FORM_OPTIONS], Field(description="Formkit elements of the work event.")] = []

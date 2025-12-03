from typing import Annotated

from aihub_lib.nats.events.form.elements.InputText import InputText
from aihub_lib.nats.events.form.Form import Form
from pydantic import Field


class HumanAWorkForm(Form):
    payload: Annotated[InputText, Field(description="Input text A")]

from typing import Annotated

from pydantic import Field

from aihub_lib.nats.events.form.Form import Form
from aihub_lib.nats.events.form.elements.InputText import InputText


class HumanAWorkForm(Form):
    payload: Annotated[InputText, Field(description="Input text A")]

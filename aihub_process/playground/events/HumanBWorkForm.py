from typing import Annotated

from aihub_lib.nats.events.form.elements.InputText import InputText
from aihub_lib.nats.events.form.Form import Form
from pydantic import Field


class HumanBWorkForm(Form):
    payload: Annotated[InputText, Field(description="Input text B")]

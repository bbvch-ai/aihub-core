from typing import Annotated

from pydantic import Field
from swiss_ai_hub.core.events.process.work.human.HumanWorkEvent import HumanWorkEvent
from swiss_ai_hub.core.form.elements.InputText import InputText


class HumanBWork(HumanWorkEvent):
    payload: Annotated[InputText | str, Field(description="Input text B")]

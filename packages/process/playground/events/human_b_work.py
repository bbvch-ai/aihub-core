from typing import Annotated

from pydantic import Field
from swiss_ai_hub.core.events.process import HumanWorkEvent
from swiss_ai_hub.core.form import InputText


class HumanBWork(HumanWorkEvent):
    payload: Annotated[InputText | str, Field(description="Input text B")]

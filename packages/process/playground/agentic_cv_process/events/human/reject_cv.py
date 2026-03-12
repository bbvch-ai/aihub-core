from typing import Annotated

from pydantic import Field
from swiss_ai_hub.core.events.process import HumanWorkEvent
from swiss_ai_hub.core.form import InputText


class RejectCV(HumanWorkEvent):
    reason: Annotated[InputText | str, Field(description="Gives a reason why this CV is rejected")]

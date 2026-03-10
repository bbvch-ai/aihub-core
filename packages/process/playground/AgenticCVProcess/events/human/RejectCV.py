from typing import Annotated

from pydantic import Field
from swiss_ai_hub.core.nats.events.form.elements.InputText import InputText
from swiss_ai_hub.core.nats.events.work.human.HumanWorkEvent import HumanWorkEvent


class RejectCV(HumanWorkEvent):
    reason: Annotated[InputText | str, Field(description="Gives a reason why this CV is rejected")]

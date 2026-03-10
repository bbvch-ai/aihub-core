from typing import Annotated

from pydantic import Field
from swiss_ai_hub.core.nats.events import HumanWorkEvent
from swiss_ai_hub.core.nats.events.form.elements.InputText import InputText


class AcceptCV(HumanWorkEvent):
    reason: Annotated[InputText | str, Field(description="Gives a reason why this CV is accepted")]

from typing import ClassVar

from swiss_ai_hub.core.nats.events import HumanWorkRequestEvent

from playground.events.HumanBWork import HumanBWork


class HumanBWorkRequest(HumanWorkRequestEvent):
    work: ClassVar[type[HumanBWork]] = HumanBWork

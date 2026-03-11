from typing import ClassVar

from swiss_ai_hub.core.events.process import HumanWorkRequestEvent

from playground.events.HumanBWork import HumanBWork


class HumanBWorkRequest(HumanWorkRequestEvent):
    work: ClassVar[type[HumanBWork]] = HumanBWork

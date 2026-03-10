from typing import ClassVar

from swiss_ai_hub.core.nats.events import HumanWorkRequestEvent

from swiss_ai_hub.api.runners.simulation.process.events.HumanBWork import HumanBWork


class HumanBWorkRequest(HumanWorkRequestEvent):
    work: ClassVar[type[HumanBWork]] = HumanBWork

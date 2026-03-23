from typing import ClassVar

from swiss_ai_hub.core.events.process import HumanWorkRequestEvent

from swiss_ai_hub.api.runners.simulation.process.events.human_b_work import HumanBWork


class HumanBWorkRequest(HumanWorkRequestEvent):
    work: ClassVar[type[HumanBWork]] = HumanBWork

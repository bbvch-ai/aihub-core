from typing import ClassVar

from aihub_lib.nats.events import HumanWorkRequestEvent

from playground.events.HumanBWork import HumanBWork


class HumanBWorkRequest(HumanWorkRequestEvent):
    work: ClassVar[type[HumanBWork]] = HumanBWork

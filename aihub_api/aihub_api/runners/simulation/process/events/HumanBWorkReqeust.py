from typing import ClassVar

from aihub_lib.nats.events import HumanWorkRequestEvent

from aihub_api.runners.simulation.process.events.HumanBWork import HumanBWork


class HumanBWorkRequest(HumanWorkRequestEvent):
    work: ClassVar[type[HumanBWork]] = HumanBWork

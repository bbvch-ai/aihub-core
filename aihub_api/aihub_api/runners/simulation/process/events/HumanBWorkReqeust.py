from typing import ClassVar

from aihub_api.runners.simulation.process.events.HumanBWork import HumanBWork
from aihub_lib.nats.events import HumanWorkRequestEvent



class HumanBWorkRequest(HumanWorkRequestEvent):
    work: ClassVar[type[HumanBWork]] = HumanBWork

from typing import ClassVar

from aihub_lib.nats.events import HumanWorkRequestEvent

from playground.events.HumanBWork import HumanBWork
from playground.events.HumanBWorkForm import HumanBWorkForm


class HumanBWorkRequest(HumanWorkRequestEvent):
    form: ClassVar[type[HumanBWorkForm]] = HumanBWorkForm  # UI definition (validated by forms list)
    work: ClassVar[type[HumanBWork]] = HumanBWork  # Data schema (used by Human.In)

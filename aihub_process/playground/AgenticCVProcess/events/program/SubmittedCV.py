from typing import List

from aihub_lib.nats.events import ProcessStartEvent
from aihub_lib.nats.events.work.program.ProgramWorkEvent import ProgramWorkEvent


class SubmittedCV(ProgramWorkEvent, ProcessStartEvent):
    name: str
    qualifications: List[str]
from typing import List

from aihub_process.process.io.program.ProgramWork import ProgramWork


class SubmittedCV(ProgramWork):
    name: str
    qualifications: List[str]
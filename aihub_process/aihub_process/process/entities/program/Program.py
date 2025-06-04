from typing import Type, TYPE_CHECKING

from aihub_process.process.entities.BaseProcessEntity import BaseProcessEntity
from aihub_lib.persistence.process.ProgramProcessStepInstanceEntity import ProgramIn as DBProgramIn, ProgramProcessStepInstanceEntity, ProgramOut as DBProgramOut
from aihub_process.process.io.program.ProgramWorkRequest import ProgramWorkRequest

class Program(BaseProcessEntity):
    class In(BaseProcessEntity.In):
        route: str
        method: str = "POST"

        def to_persisted(self) -> DBProgramIn:
            return DBProgramIn(route=self.route, method=self.method)

    class Out(BaseProcessEntity.Out):
        endpoint: str
        method: str = "POST"

        def to_persisted(self) -> DBProgramOut:
            return DBProgramOut(endpoint=self.endpoint, method=self.method)

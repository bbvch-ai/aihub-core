from aihub_lib.persistence.process.ProgramProcessStepInstanceEntity import ProgramIn as DBProgramIn, ProgramOut as DBProgramOut
from aihub_process.delegators.AbstractProcessEntity import BaseProcessEntity


class Program(BaseProcessEntity):
    class In(BaseProcessEntity.In):
        route: str
        method: str = "POST"


    class Out(BaseProcessEntity.Out):
        endpoint: str
        method: str = "POST"


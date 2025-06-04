from typing import Type, TYPE_CHECKING

from pydantic import BaseModel

from aihub_process.process.entities.BaseProcessEntity import BaseProcessEntity
from aihub_lib.persistence.process.ProcessStepInstanceEntity import TerminalOut as DBTerminalOut, \
    ProcessStepInstanceEntity


class Terminal(BaseProcessEntity):
    class Out(BaseProcessEntity.Out):
        def to_persisted(self) -> DBTerminalOut:
            from aihub_lib.persistence.process.ProcessStepInstanceEntity import TerminalOut as DBTerminalOut
            return DBTerminalOut()

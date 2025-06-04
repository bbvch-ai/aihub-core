import abc
from typing import TypeVar, Type

from pydantic import BaseModel

from aihub_lib.persistence.process.ProcessStepInstanceEntity import BaseProcessEntityIn as DBBaseProcessEntityIn
from aihub_lib.persistence.process.ProcessStepInstanceEntity import BaseProcessEntityOut as DBBaseProcessEntityOut

PydanticInT = TypeVar('PydanticInT', bound='BaseProcessEntity.In')
PydanticOutT = TypeVar('PydanticOutT', bound='BaseProcessEntity.Out')
DBInT = TypeVar('DBInT', bound=DBBaseProcessEntityIn)
DBOutT = TypeVar('DBOutT', bound=DBBaseProcessEntityOut)

class BaseProcessEntity(abc.ABC):
    class In(BaseModel, abc.ABC):
        @abc.abstractmethod
        def to_persisted(self) -> DBBaseProcessEntityIn:
            pass

    class Out(BaseModel, abc.ABC):
        @abc.abstractmethod
        def to_persisted(self) -> DBBaseProcessEntityOut:
            pass

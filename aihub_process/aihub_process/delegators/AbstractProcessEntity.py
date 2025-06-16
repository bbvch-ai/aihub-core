import abc

from pydantic import BaseModel



class BaseProcessEntity(abc.ABC):
    class In(BaseModel, abc.ABC):
        pass

    class Out(BaseModel, abc.ABC):
        pass

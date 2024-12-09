import logging
import os
import threading
import time
from datetime import datetime

from bson import ObjectId
from pydantic import BaseModel, Field, computed_field, ConfigDict, PrivateAttr
from typing import Type, ClassVar, Dict, Optional, Any
import json

logger = logging.getLogger(__name__)


class BaseEvent(BaseModel):
    _event_registry: ClassVar[Dict[str, Type["BaseEvent"]]] = {}
    event_id: str = Field(default_factory=lambda: str(ObjectId()))
    created_at: int = Field(
        default_factory=time.time_ns,
        description="The time the event was stored in the distributed event store",
    )

    # In case an unknown event type is deserialized, we store its original type here
    _unknown_type: Optional[str] = PrivateAttr(None)
    _unknown_data: Optional[Dict[str, Any]] = PrivateAttr(None)

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        populate_by_name=True,
        use_enum_values=True,
    )

    @computed_field  # type: ignore[misc]
    @property
    def _type(self) -> str:
        return self._unknown_type or self.__class__.__name__

    @classmethod
    def __pydantic_init_subclass__(cls, **kwargs: Any) -> None:
        super().__pydantic_init_subclass__(**kwargs)
        logging.debug("Registering", cls.__name__)
        BaseEvent._event_registry[cls.__name__] = cls

    @classmethod
    def deserialize_event(cls, data: bytes | str | Dict[str, Any]) -> "BaseEvent":
        if isinstance(data, dict):
            json_data = data
        elif isinstance(data, str):
            json_data = json.loads(data)
        elif isinstance(data, bytes):
            json_data = json.loads(data.decode())
        else:
            raise ValueError(f"Cannot deserialize data of type {type(data)}")
        event_type = json_data.get("_type")
        if event_type and type(event_type) is str:
            event_class = cls._event_registry.get(event_type)
            if event_class:
                return event_class(**json_data)
        logger.warning(
            f"Unknown event type: {event_type}. Registring as generic 'BaseEvent'? Known are: {BaseEvent._event_registry.keys()}"
        )
        return cls(_unknown_type=event_type, **json_data, _unknown_data=json_data)

    def to_trace_dict(self) -> Dict[str, Any]:
        event_dict = {
            **self.model_dump(),
            "os_pid": os.getpid(),
            "os_threadid": threading.get_ident(),
        }
        created_at = event_dict["created_at"]

        created_datetime = datetime.fromtimestamp(created_at / 1_000_000_000)
        event_dict["created_at"] = created_datetime.strftime("%Y-%m-%d %H:%M:%S.%f") + f"{created_at % 1_000:03d}"
        return event_dict

    def model_dump(self, **kwargs: Any) -> Dict[str, Any]:
        data = super().model_dump(**kwargs)
        if not self._unknown_data:
            return data
        return {
            **self._unknown_data,
            **data,
        }

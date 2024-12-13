import logging
from typing import ClassVar, Dict, Type, Any

from pydantic import BaseModel

logger = logging.getLogger(__name__)


class Topic(BaseModel):
    _topic_registry: ClassVar[Dict[str, Type["Topic"]]] = {}

    @classmethod
    def __pydantic_init_subclass__(cls, **kwargs: Any) -> None:
        super().__pydantic_init_subclass__(**kwargs)
        if cls.__name__ != "Topic":
            logger.debug(f"Registering Topic {cls.__name__}")
            Topic._topic_registry[cls.__name__] = cls

    @classmethod
    def from_subject(cls, subject: str) -> "Topic":
        for topic_type, topic_class in Topic._topic_registry.items():
            try:
                return topic_class.from_subject(subject)
            except (ValueError, AssertionError):
                pass
        raise ValueError(f"Could not parse topic from subject: {subject}")
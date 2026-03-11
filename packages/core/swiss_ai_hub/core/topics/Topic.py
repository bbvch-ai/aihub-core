import abc
import logging
from typing import Any, ClassVar, Self

from pydantic import BaseModel

logger = logging.getLogger(__name__)


class Topic(BaseModel, abc.ABC):
    """
    Base class for representing structured topics.

    ### Why This Class Exists
    Many event-driven architectures rely on predefined patterns or formats for message subjects.
    The `Topic` class serves as a root for various specialized topic classes, each capable of
    parsing and representing a specific pattern. By subclassing `Topic` and implementing a
    `from_subject` method, developers create new topic types that can handle different domains
    or message formats.

    ### Automatic Registration of Subclasses
    Through the `__pydantic_init_subclass__` hook, every time a `Topic` subclass is defined, it
    is registered in the `_topic_registry`. This registry allows the `Topic.from_subject` method
    to dynamically discover and attempt all known topic classes until it finds one that can parse
    the given subject.

    ### Benefits
    - **Extensibility:** Add a new topic type by creating a subclass; it's automatically registered.
    - **Decoupling:** No need for a central "if/else" or map of subject patterns. Subclasses handle
      their own parsing logic.
    - **Maintainability:** Changes to topic parsing are localized to the relevant subclass without
      affecting others.
    """

    _topic_registry: ClassVar[dict[str, type["Topic"]]] = {}

    @property
    @abc.abstractmethod
    def execution_context_id(self) -> str:
        """
        The execution context ID of a topic is usually the most narrow ID that groups events logically together.
        For example, in Agents, the most narrow grouping is the run_id. For Processes, it is the walkthrough_id.
        """
        pass

    @classmethod
    def __pydantic_init_subclass__(cls, **kwargs: Any) -> None:
        """
        Called by Pydantic whenever a new subclass is created.

        Registers the subclass in the global `_topic_registry` unless it's the base `Topic` class itself.
        This enables the dynamic discovery of available topic types without manual maintenance.
        """
        super().__pydantic_init_subclass__(**kwargs)
        if cls.__name__ != "Topic":
            logger.debug(f"Registering Topic {cls.__name__}")
            Topic._topic_registry[cls.__name__] = cls

    @classmethod
    @abc.abstractmethod
    def from_subject(cls, subject: str) -> Self:
        """
        Attempts to parse a subject string using all known `Topic` subclasses in the registry.

        It tries each registered subclass's `from_subject` method. The first one that successfully
        parses the subject returns an instance. If none succeed, a ValueError is raised.

        Use this method when you need to handle arbitrary subjects, letting the topic classes
        themselves decide if the subject matches their pattern.
        """
        if cls is not Topic:
            # If this method is called on a subclass, it means the subclass has not
            # overridden it. In this case, we should indicate failure to prevent recursion.
            raise ValueError(f"'{cls.__name__}' does not implement 'from_subject' and cannot parse subject '{subject}'")

        for topic_type, topic_class in Topic._topic_registry.items():
            try:
                return topic_class.from_subject(subject)
            except (ValueError, AssertionError):
                # This subclass couldn't parse the subject; try the next one
                pass
        raise ValueError(f"Could not parse topic from subject: {subject}")

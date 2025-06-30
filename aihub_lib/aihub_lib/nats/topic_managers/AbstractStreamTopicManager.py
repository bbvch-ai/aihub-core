import abc
from typing import Tuple


class AbstractStreamTopicManager(abc.ABC):
    @abc.abstractmethod
    def get_stream(self) -> Tuple[str, str]:
        pass

    @abc.abstractmethod
    def get_subject_for_all_control_events(self) -> str:
        pass

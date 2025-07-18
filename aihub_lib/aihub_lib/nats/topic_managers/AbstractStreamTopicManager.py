import abc


class AbstractStreamTopicManager(abc.ABC):
    @abc.abstractmethod
    def get_stream(self) -> tuple[str, str]:
        pass

    @abc.abstractmethod
    def get_subject_for_all_control_events(self) -> str:
        pass

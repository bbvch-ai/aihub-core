from abc import abstractmethod

from lib_core.nats.events import DisplayEvent


class CostEvent(DisplayEvent):

    @abstractmethod
    def get_total_costs(self) -> float:
        pass
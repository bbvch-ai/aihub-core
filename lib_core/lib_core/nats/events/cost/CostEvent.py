from abc import abstractmethod

from ..display import DisplayEvent


class CostEvent(DisplayEvent):

    @abstractmethod
    def get_total_costs(self) -> float:
        pass
from abc import abstractmethod
from typing import ClassVar

from swiss_ai_hub.core.events.agent.display.display_event import DisplayEvent
from swiss_ai_hub.core.i18n.locale_string import LocaleString


class CostEvent(DisplayEvent):
    """
    An abstract base class representing a cost-related event visible to end-users or
    dashboards. While `ControlEvent` influences system flow, `CostEvent` is strictly
    informational, providing insights into resource usage or financial costs incurred during
    the processing of requests.

    ### Why CostEvent?
    Monitoring and displaying costs is crucial in systems that use external paid services,
    like Large Language Model queries. By surfacing these events as display-only, operators
    and end-users can understand and optimize usage without altering workflow logic.

    ### Key Point
    - Implementers of `CostEvent` must define `get_total_costs()` to compute the aggregate cost.
    """

    _display_name: ClassVar[LocaleString] = LocaleString.from_i18n_path("lib.events.cost_event.name")
    _display_description: ClassVar[LocaleString] = LocaleString.from_i18n_path("lib.events.cost_event.description")

    @abstractmethod
    def get_total_costs(self) -> float:
        """
        Return the total cost associated with this event. Implementations may aggregate multiple cost
        components (e.g., prompt tokens, completion tokens, embeddings) into a single value.
        """
        pass

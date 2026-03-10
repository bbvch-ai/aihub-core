import inspect
from typing import Annotated, TypeVar, cast

from pydantic import Field

from swiss_ai_hub.core.nats.events.control.stop.StopEvent import StopEvent
from swiss_ai_hub.core.nats.events.utils import get_base_type
from swiss_ai_hub.core.nats.events.work.WorkEvent import WorkEvent
from swiss_ai_hub.core.nats.topics.agents import AgentInstanceTopic, PartialAgentTopic

TEvent = TypeVar("TEvent", bound=StopEvent)


class AgentWorkEvent[TEvent: StopEvent](WorkEvent):
    """
    Signals a piece of work completed by another agent.
    As this work event is generated automatically by the agent delegator, you can't really add attributes to this
    class.
    The delegator will add the stop event type to the `agent_stop_event` field, making the information
    from the agents stop event accessible for you to use in your process step.
    """

    submitted_by: Annotated[
        AgentInstanceTopic | PartialAgentTopic, Field(description="The topic of the agent that submitted the work.")
    ]
    agent_stop_event: Annotated[TEvent, Field(description="The stop event of the agent that completed the work.")]

    @classmethod
    def get_stop_event_type(cls) -> tuple[type[StopEvent], ...]:
        """
        Extracts the concrete stop event type(s) from the `agent_stop_event` field.
        This version uses Pydantic's `model_fields` for robust type resolution
        before unwrapping complex type hints.
        """
        if cls is AgentWorkEvent:
            raise TypeError("Cannot get stop event type from the non-specialized generic base class 'AgentWorkEvent'.")

        field_info = cls.model_fields.get("agent_stop_event")

        if not field_info or not field_info.annotation:
            raise ValueError(f"Could not find a typed 'agent_stop_event' attribute on '{cls.__name__}'.")

        field_annotation = field_info.annotation
        base_types = get_base_type(field_annotation)

        if not base_types:
            raise ValueError(
                f"Unable to extract a base type from the annotation for 'agent_stop_event' in '{cls.__name__}'."
            )

        for t in base_types:
            if not inspect.isclass(t):
                raise TypeError(f"Extracted type '{t}' is not a class. Full annotation was '{field_annotation}'.")

        return cast(tuple[type[StopEvent], ...], base_types)

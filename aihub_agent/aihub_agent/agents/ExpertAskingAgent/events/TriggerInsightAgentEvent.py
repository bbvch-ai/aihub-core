from aihub_lib.nats.events import ControlEvent


class TriggerInsightAgentEvent(ControlEvent):
    """Event indicating that the InsightAgent should be triggered with the expert conversation data."""

    expert_answer: str

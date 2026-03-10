from swiss_ai_hub.core.nats.events import StopEvent


class NoAnswerStopEvent(StopEvent):
    """Event representing the experts unability to answer the users question."""

    pass

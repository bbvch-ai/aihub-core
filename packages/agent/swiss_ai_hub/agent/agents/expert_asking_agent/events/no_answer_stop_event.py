from swiss_ai_hub.core.events.agent import StopEvent


class NoAnswerStopEvent(StopEvent):
    """Event representing the experts unability to answer the users question."""

    pass

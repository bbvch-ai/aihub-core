from swiss_ai_hub.core.nats.events import ControlEvent


class UserRequestsExpertEvent(ControlEvent):
    """
    Event signaling that a user has consented to expert escalation.

    This event is emitted when the user confirms they want their question
    to be forwarded to a human expert after the system determined that
    the available context is insufficient to answer their query.
    """

    pass

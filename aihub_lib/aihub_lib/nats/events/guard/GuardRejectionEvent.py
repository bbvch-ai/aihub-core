from pydantic import Field

from ..control import StopEvent


class GuardRejectionEvent(StopEvent):
    """
    A class representing a guard rejection event.
    This event is used to communicate the reason for the rejection to the client.


    ### Why GuardRejectionEvent?
    Safeguarding the system from invalid requests is a critical part of any system. This event
    is used to communicate the reason for the rejection to the client.
    """

    reason: str = Field(..., description="Reason why the Guard rejected the request.")

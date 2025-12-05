"""Event signaling user has consented to expert escalation."""

from aihub_lib.nats.events import ControlEvent


class UserConsentEvent(ControlEvent):
    """Event signaling that the user has consented to contact an expert."""

    pass

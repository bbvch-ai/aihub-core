from aihub_lib.generative_ai.user.User import User
from aihub_lib.nats.events.Event import Event


class SlackResponseReceivedEvent(Event):
    """Event emitted when a response is received from Slack"""

    response: str
    expert_name: str
    channel_id: str
    message_ts: str
    thread_ts: str | None
    user: User

from aihub_lib.generative_ai.user.User import User
from aihub_lib.nats.events.Event import Event


class SlackMessagePostedEvent(Event):
    """Event emitted when a message is successfully posted to Slack"""

    question: str
    channel_id: str
    message_ts: str
    thread_ts: str | None
    user: User

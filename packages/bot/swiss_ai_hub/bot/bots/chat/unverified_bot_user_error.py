class UnverifiedBotUserError(Exception):
    """Raised when an activity carries no channel-verified way to tell who sent it.

    The sender controls display names and most activity fields, so only identities the channel itself vouches for
    (the Teams member lookup, the Slack user profile) may map a bot user to a platform account.
    """

    def __init__(self, channel_id: str | None, reason: str) -> None:
        self.channel_id = channel_id
        super().__init__(f"Cannot verify the sender of a '{channel_id}' activity: {reason}")

class BotAccessDeniedError(Exception):
    """Raised when the resolved bot user may not use the agent or model the bot endpoint is bound to."""

    def __init__(self, user_id: str, resource: str) -> None:
        self.user_id = user_id
        self.resource = resource
        super().__init__(f"User {user_id} does not have access to {resource}")

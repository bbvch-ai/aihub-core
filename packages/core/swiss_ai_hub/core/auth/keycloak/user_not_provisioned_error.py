class UserNotProvisionedError(Exception):
    """Raised when a bot user has no Keycloak account.

    Keycloak provisions federated users lazily via its first-broker-login flow, which only runs on
    an OIDC browser login. A user who reaches the platform through a bot first (authenticated via
    Azure Bot Service credentials) therefore has no account, and the platform deliberately offers no
    bot-driven provisioning path (ADR `2026_06_08_no_bot_first_keycloak_provisioning`). Callers
    surface this to the user as an actionable "sign in to the Hub first" message rather than a
    generic error.
    """

    def __init__(self, email: str) -> None:
        self.email = email
        super().__init__(f"User with email '{email}' is not provisioned in Keycloak")

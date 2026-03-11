from swiss_ai_hub.core.auth.dependencies.dangerous_development_only_auth_handler.dangerous_development_only_auth_settings import (  # noqa: E501
    DangerousDevelopmentOnlyAuthSettings,
)
from swiss_ai_hub.core.auth.identity.user_identity import UserIdentity


def fake_user() -> UserIdentity:
    return DangerousDevelopmentOnlyAuthSettings().get_user_identity()

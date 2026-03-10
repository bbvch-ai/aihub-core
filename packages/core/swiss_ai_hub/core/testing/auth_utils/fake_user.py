from swiss_ai_hub.core.auth.dependencies.DangerousDevelopmentOnlyAuthHandler.DangerousDevelopmentOnlyAuthSettings import (
    DangerousDevelopmentOnlyAuthSettings,
)
from swiss_ai_hub.core.auth.identity.UserIdentity import UserIdentity


def fake_user() -> UserIdentity:
    return DangerousDevelopmentOnlyAuthSettings().get_user_identity()

from aihub_lib.auth.dependencies.DangerousDevelopmentOnlyAuthHandler.DangerousDevelopmentOnlyAuthSettings import (
    DangerousDevelopmentOnlyAuthSettings,
)
from aihub_lib.auth.identity.UserIdentity import UserIdentity


def fake_user() -> UserIdentity:
    return DangerousDevelopmentOnlyAuthSettings().get_user_identity()

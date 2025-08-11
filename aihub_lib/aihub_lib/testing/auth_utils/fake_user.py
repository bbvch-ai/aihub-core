from aihub_lib.auth.dependencies.DangerousDevelopmentOnlyAuthHandler.DangerousDevelopmentOnlyAuthSettings import (
    DangerousDevelopmentOnlyAuthSettings,
)
from aihub_lib.auth.identity.UserIdentity import UserIdentity


def fake_user() -> UserIdentity:
    return UserIdentity(
        name=DangerousDevelopmentOnlyAuthSettings().NAME,
        email=DangerousDevelopmentOnlyAuthSettings().EMAIL,
        id=DangerousDevelopmentOnlyAuthSettings().OID,
        roles=DangerousDevelopmentOnlyAuthSettings().ROLES,
    )

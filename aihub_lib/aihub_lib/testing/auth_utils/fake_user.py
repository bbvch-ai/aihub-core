import uuid

from aihub_lib.auth.AuthenticatedUser import AuthenticatedUser


def fake_user() -> AuthenticatedUser:
    return AuthenticatedUser(
        name="Fake User",
        preferred_username="fake@user.com",
        oid=str(uuid.uuid4()),
        roles=["AllAgents"],
    )

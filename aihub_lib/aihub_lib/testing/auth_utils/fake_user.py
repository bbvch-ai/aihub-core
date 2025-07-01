import uuid

from aihub_lib.auth.identity.UserIdentity import UserIdentity


def fake_user() -> UserIdentity:
    return UserIdentity(
        name="Fake User",
        email="fake@user.com",
        id=str(uuid.uuid4()),
        roles=["aihub.user.agent.>"],
    )

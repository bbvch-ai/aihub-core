from pydantic import BaseModel

from api_core.auth.AuthenticatedUser import AuthenticatedUser


class UserDTO(BaseModel):
    id: str
    name: str
    email: str

    @classmethod
    def from_authenticated_user(cls, user: AuthenticatedUser):
        return cls(
            id=user.oid,
            name=user.name,
            email=user.preferred_username,
        )

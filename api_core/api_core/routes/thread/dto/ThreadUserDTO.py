from pydantic import BaseModel

from lib_core.persistence.messaging.entities.ThreadEntity import User


class ThreadUserDTO(BaseModel):
    user_id: str

    @classmethod
    def from_user_entity(cls, entity: User):
        return cls(
            user_id=entity.user_id
        )
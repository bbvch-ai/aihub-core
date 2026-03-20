from pydantic import BaseModel


class AddUserRequest(BaseModel):
    user_id: str

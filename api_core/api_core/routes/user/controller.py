from fastapi import APIRouter, Depends

from api_core.depends.user import user_from_token
from api_core.dto.User import User

user_router = APIRouter()

@user_router.get("/user")
async def get_user(
        user: User = Depends(user_from_token),
) -> User:
    return user

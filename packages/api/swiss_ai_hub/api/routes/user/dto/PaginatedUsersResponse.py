from typing import Annotated

from pydantic import Field

from swiss_ai_hub.api.pagination.PageDTO import PageDTO
from swiss_ai_hub.api.routes.user.dto.UserDTO import UserDTO


class PaginatedUsersResponse(PageDTO):
    """
    Represents a paginated response containing a list of users.
    """

    users: Annotated[list[UserDTO], Field(description="List of MinimalUserDTO objects for the current page.")]

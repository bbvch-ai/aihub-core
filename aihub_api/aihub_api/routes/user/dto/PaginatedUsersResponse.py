from typing import Annotated

from pydantic import Field

from aihub_api.pagination.PageDTO import PageDTO
from aihub_api.routes.user.dto.UserDTO import UserDTO


class PaginatedUsersResponse(PageDTO):
    """
    Represents a paginated response containing a list of users.
    """

    users: Annotated[list[UserDTO], Field(description="List of MinimalUserDTO objects for the current page.")]

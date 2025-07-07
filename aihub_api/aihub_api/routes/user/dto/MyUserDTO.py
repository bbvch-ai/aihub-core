from typing import Annotated

from pydantic import Field

from aihub_api.routes.user.dto.Dashboard.DashboardDTO import DashboardDTO
from aihub_api.routes.user.dto.UserDTO import UserDTO


class MyUserDTO(UserDTO):
    dashboard: Annotated[DashboardDTO | None, Field(description="User dashboard configuration for index page")] = None
    favorite_modules: Annotated[list[str], Field(description="List of favorite modules from aihub suite")] = []
    roles: Annotated[list[str], Field(description="List of roles assigned to the user")] = []

from typing import Annotated, List, Optional

from pydantic import Field

from aihub_api.routes.user.dto.Dashboard.DashboardDTO import DashboardDTO
from aihub_api.routes.user.dto.UserDTO import UserDTO


class MyUserDTO(UserDTO):
    dashboard: Annotated[Optional[DashboardDTO], Field(description="User dashboard configuration for index page")] = (
        None
    )
    favorite_modules: Annotated[List[str], Field(description="List of favorite modules from aihub suite")] = []
    roles: Annotated[List[str], Field(description="List of roles assigned to the user")] = []

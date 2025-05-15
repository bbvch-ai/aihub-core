from typing import List, Optional

from pydantic import Field

from aihub_api.routes.user.dto.Dashboard.DashboardDTO import DashboardDTO
from aihub_api.routes.user.dto.UserDTO import UserDTO


class MyUserDTO(UserDTO):
    dashboard: Optional[DashboardDTO] = Field(None, description="User dashboard configuration for index page")
    favorite_modules: List[str] = Field(default_factory=list, description="List of favorite modules from aihub suite")
    roles: List[str] = Field(default_factory=list, description="List of roles assigned to the user")

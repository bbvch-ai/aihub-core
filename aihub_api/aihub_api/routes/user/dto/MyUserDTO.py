from typing import List, Optional

from pydantic import Field

from aihub_api.routes.user.dto.Dashboard.DashboardDTO import DashboardDTO
from aihub_api.routes.user.dto.UserDTO import UserDTO


class MyUserDTO(UserDTO):
    dashboard: Optional[DashboardDTO] = None
    favorite_modules: List[str] = Field(default_factory=list)
    roles: List[str] = Field(default_factory=list)

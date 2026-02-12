from datetime import datetime
from typing import Annotated

from aihub_lib.persistence.access.entities.RoleEntity import RoleEntity
from aihub_lib.persistence.user.UserEntity import UserEntity
from pydantic import Field

from aihub_api.routes.user.dto.Dashboard.DashboardDTO import DashboardDTO
from aihub_api.routes.user.dto.MinimalUserDTO import MinimalUserDTO


class UserDTO(MinimalUserDTO):
    last_accessed: Annotated[datetime, Field(description="Last time the user was updated")]
    roles: Annotated[list[str], Field(description="List of roles assigned to the user")] = []
    favorite_modules: Annotated[list[str], Field(description="List of favorite modules from aihub suite")] = []
    dashboard: Annotated[DashboardDTO | None, Field(description="User dashboard configuration for index page")] = None

    @classmethod
    def from_user_entity(cls, user_entity: UserEntity):
        dashboard_data = user_entity.dashboard.to_mongo()
        dashboard_dto = DashboardDTO(**dashboard_data)

        valid_roles = RoleEntity.filter_existing_roles(user_entity.get_roles())

        return cls(
            id=user_entity.id,
            name=user_entity.name,
            email=user_entity.email,
            profile_image=user_entity.profile_image,
            dashboard=dashboard_dto,
            favorite_modules=user_entity.favorite_modules,
            roles=valid_roles,
            last_accessed=user_entity.last_updated,
        )

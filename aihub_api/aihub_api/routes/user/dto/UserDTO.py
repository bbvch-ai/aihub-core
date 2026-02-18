from datetime import datetime
from typing import Annotated

from aihub_lib.persistence.user.UserEntity import UserEntity
from pydantic import Field

from aihub_api.routes.user.dto.Dashboard.DashboardDTO import DashboardDTO
from aihub_api.routes.user.dto.MinimalUserDTO import MinimalUserDTO


class UserDTO(MinimalUserDTO):
    last_accessed: Annotated[datetime, Field(description="Last time the user was updated")]
    favorite_modules: Annotated[list[str], Field(description="List of favorite modules from aihub suite")] = []
    dashboard: Annotated[DashboardDTO | None, Field(description="User dashboard configuration for index page")] = None

    @classmethod
    def from_user_entity(cls, user_entity: UserEntity):
        """
        Create a UserDTO from a UserEntity.
        Note: roles are not populated here as they require tenant context.
        Use UserWithAccessDTO for role-aware user information.
        """
        dashboard_data = user_entity.dashboard.to_mongo()
        dashboard_dto = DashboardDTO(**dashboard_data)

        return cls(
            id=user_entity.id,
            name=user_entity.name,
            email=user_entity.email,
            profile_image=user_entity.profile_image,
            dashboard=dashboard_dto,
            favorite_modules=user_entity.favorite_modules,
            last_accessed=user_entity.last_updated,
        )

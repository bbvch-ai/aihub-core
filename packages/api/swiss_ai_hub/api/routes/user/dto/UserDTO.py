from datetime import datetime
from typing import Annotated

from pydantic import Field
from swiss_ai_hub.core.persistence.user.UserEntity import UserEntity

from swiss_ai_hub.api.routes.user.dto.Dashboard.DashboardDTO import DashboardDTO
from swiss_ai_hub.api.routes.user.dto.MinimalUserDTO import MinimalUserDTO


class UserDTO(MinimalUserDTO):
    last_accessed: Annotated[datetime, Field(description="Last time the user was updated")]
    favorite_modules: Annotated[list[str], Field(description="List of favorite modules from aihub suite")] = []
    dashboard: Annotated[DashboardDTO | None, Field(description="User dashboard configuration for index page")] = None

    @classmethod
    def from_user_entity(cls, user_entity: UserEntity):
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

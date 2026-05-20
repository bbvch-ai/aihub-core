from pydantic import BaseModel, Field


class WhoamiResponse(BaseModel):
    is_sys_admin: bool = Field(description="Whether the authenticated user has the AIHubSysAdmin Keycloak realm role.")

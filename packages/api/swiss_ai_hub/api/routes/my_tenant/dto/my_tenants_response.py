from typing import Annotated

from pydantic import BaseModel, Field

from swiss_ai_hub.api.routes.my_tenant.dto.tenant_membership_dto import TenantMembershipDTO


class MyTenantsResponse(BaseModel):
    """Response for the GET /my-tenants endpoint, including sysadmin status."""

    tenants: Annotated[list[TenantMembershipDTO], Field(description="Tenants the current user belongs to")]
    is_sys_admin: Annotated[bool, Field(description="Whether the user has system administrator privileges")] = False

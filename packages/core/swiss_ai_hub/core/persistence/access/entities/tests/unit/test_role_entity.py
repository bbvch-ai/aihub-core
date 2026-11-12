from unittest.mock import patch

import pytest

from swiss_ai_hub.core.auth.realm_roles import SYS_ADMIN_ROLE
from swiss_ai_hub.core.persistence.access.entities.role_entity import RoleEntity

pytestmark = pytest.mark.asyncio


async def test_sys_admin_role_name_is_reserved() -> None:
    """Every tenant's OpenWebUI sysadmin group is named after the realm role, so a tenant role must not share it."""
    with patch.object(RoleEntity, "insert") as insert, pytest.raises(ValueError, match="reserved"):
        await RoleEntity.create_tenant_role(name=SYS_ADMIN_ROLE, description="", access_rules=[], tenant_id="t1")

    insert.assert_not_called()

"""Deterministic test identity constants and helpers.

Test identity is deterministic and not configurable via environment variables,
so plain module-level constants are the right shape. Tests and playground
servers build a ``UserIdentity`` from these constants via :func:`fake_user`;
:class:`TestAuthHandler` uses them as the acting principal when mounted as a
controller's auth dependency.

Deliberately lives under ``swiss_ai_hub.core.testing`` so it is not reachable
through ``swiss_ai_hub.core.auth``. Production code cannot import it by
accident; the namespace boundary is the safety mechanism.
"""

from swiss_ai_hub.core.auth.identity.tenant_identity import TenantIdentity
from swiss_ai_hub.core.auth.identity.user_identity import UserIdentity

TEST_USER_OID = "68b1df1f4fa54f9aeab2e6b7"
TEST_USER_NAME = "Dev User"
TEST_USER_EMAIL = "dev@swissaihub.local"
TEST_USER_ROLES = ["TestOnlyFullAdminAccess"]

TEST_TENANT_ID = "__test_tenant__"
TEST_TENANT_NAME = "Test Tenant"
TEST_TENANT_ACCESS_RULES = ["aihub.admin.>"]


def fake_tenant_identity() -> TenantIdentity:
    return TenantIdentity(
        id=TEST_TENANT_ID,
        name=TEST_TENANT_NAME,
        access_rules=list(TEST_TENANT_ACCESS_RULES),
    )


def fake_user(is_sys_admin: bool = False) -> UserIdentity:
    """Builds a ``UserIdentity`` suitable for tests and agent triggers.

    The identity is self-contained — ``acting_within_tenant`` is embedded so the
    returned user can be used directly where ``AccessChecker.from_user`` or
    tenant-scoped controllers expect a resolved tenant context.
    """
    return UserIdentity(
        id=TEST_USER_OID,
        name=TEST_USER_NAME,
        email=TEST_USER_EMAIL,
        roles=list(TEST_USER_ROLES),
        acting_within_tenant=fake_tenant_identity(),
        is_sys_admin=is_sys_admin,
    )

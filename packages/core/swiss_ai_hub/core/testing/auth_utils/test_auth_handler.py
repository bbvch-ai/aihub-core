"""Test-only auth handler.

Lives under ``swiss_ai_hub.core.testing`` so it is not reachable through the
production ``swiss_ai_hub.core.auth`` public interface. Intended for pytest
playground tests and for interactive playground servers (``python main.py`` in
``packages/*/playground/**``) where bypassing token verification is desirable.
NEVER used by production entry points or mounted by ``packages/*/app/``
deployments.

The handler bypasses token parsing and returns the constant ``TEST_USER_OID``
identity. To make tenant-scoped flows work end-to-end, it seeds a role row for
the test user in the default tenant on every call and sets an active-tenant
attribute if one is not present, then delegates to
``AuthHandler.build_identity()`` so the normal Keycloak-first membership
pipeline runs (with mocks in pytest, with the real dev Keycloak interactively).
"""

import logging

from fastapi import Request

from swiss_ai_hub.core.auth.dependencies.auth_handler import AuthHandler
from swiss_ai_hub.core.auth.identity.user_identity import UserIdentity
from swiss_ai_hub.core.auth.keycloak.keycloak_admin_service import KeycloakAdminService
from swiss_ai_hub.core.persistence.access.entities.tenant_metadata_entity import TenantMetadataEntity
from swiss_ai_hub.core.persistence.access.entities.user_tenant_role_entity import UserTenantRoleEntity
from swiss_ai_hub.core.testing.auth_utils.test_identity import (
    TEST_USER_EMAIL,
    TEST_USER_NAME,
    TEST_USER_OID,
    TEST_USER_ROLES,
)

logger = logging.getLogger(__name__)


class TestAuthHandler(AuthHandler):
    """Bypass-auth handler for playground servers and pytest-driven integration tests."""

    async def __call__(self, request: Request) -> UserIdentity:
        return await self.authenticate_token("", request)

    async def authenticate_token(self, token_str: str, request: Request | None = None) -> UserIdentity:
        logger.warning("TestAuthHandler is active — no authentication performed. Do not use in production.")

        default_tenant = TenantMetadataEntity.get_startup_tenant_metadata()
        if default_tenant:
            UserTenantRoleEntity.create_or_update(
                user_id=TEST_USER_OID,
                tenant_id=str(default_tenant.id),
                roles=list(TEST_USER_ROLES),
                validate_roles=False,
            )
            active_tenant_id = await KeycloakAdminService.get_active_tenant_id(TEST_USER_OID)
            if not active_tenant_id:
                await KeycloakAdminService.set_active_tenant(TEST_USER_OID, str(default_tenant.id))

        return await self.build_identity(
            user_id=TEST_USER_OID,
            name=TEST_USER_NAME,
            email=TEST_USER_EMAIL,
            request=request,
        )

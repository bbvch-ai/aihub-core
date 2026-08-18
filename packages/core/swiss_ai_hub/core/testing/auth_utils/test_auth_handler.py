"""Test-only auth handler.

Lives under ``swiss_ai_hub.core.testing`` so it is not reachable through the
production ``swiss_ai_hub.core.auth`` public interface. Intended for pytest
playground tests and for interactive playground servers (``python main.py`` in
``packages/*/playground/**``) where bypassing token verification is desirable.
NEVER used by production entry points or mounted by ``packages/*/app/``
deployments.

The handler bypasses token parsing and returns the constant ``TEST_USER_OID``
identity. To make tenant-scoped flows work end-to-end, it seeds a role row for
the test user in the default tenant on every call, then delegates to
``AuthHandler.build_identity()``.

Tenant resolution is overridden to read MongoDB instead of Keycloak. ``TEST_USER_OID``
is a MongoDB ObjectId, so it can never name a Keycloak user: the production pipeline's
``get_user`` lookup always 404s. pytest concealed that by mocking
``KeycloakAdminService``, while an interactive playground server against a real dev
Keycloak returned 500 on every tenant-scoped request. Since the handler already
fabricates the identity, asking the identity provider about it was never meaningful.
"""

import logging

from fastapi import HTTPException, Request

from swiss_ai_hub.core.auth.dependencies.auth_handler import AuthHandler
from swiss_ai_hub.core.auth.identity.tenant_identity import TenantIdentity
from swiss_ai_hub.core.auth.identity.user_identity import UserIdentity
from swiss_ai_hub.core.persistence.access.entities.role_entity import RoleEntity
from swiss_ai_hub.core.persistence.access.entities.tenant_metadata_entity import TenantMetadataEntity
from swiss_ai_hub.core.persistence.access.entities.user_tenant_role_entity import UserTenantRoleEntity
from swiss_ai_hub.core.testing.auth_utils.test_identity import (
    TEST_TENANT_ACCESS_RULES,
    TEST_USER_EMAIL,
    TEST_USER_NAME,
    TEST_USER_OID,
    TEST_USER_ROLES,
)

TEST_USER_ROLE_NAME = TEST_USER_ROLES[0]

logger = logging.getLogger(__name__)


class TestAuthHandler(AuthHandler):
    """Bypass-auth handler for playground servers and pytest-driven integration tests."""

    async def __call__(self, request: Request) -> UserIdentity:
        return await self.authenticate_token("", request)

    async def authenticate_token(self, token_str: str, request: Request | None = None) -> UserIdentity:
        logger.warning("TestAuthHandler is active — no authentication performed. Do not use in production.")

        default_tenant = TenantMetadataEntity.get_startup_tenant_metadata()
        if default_tenant:
            self._seed_test_role(str(default_tenant.id))
            UserTenantRoleEntity.create_or_update(
                user_id=TEST_USER_OID,
                tenant_id=str(default_tenant.id),
                roles=list(TEST_USER_ROLES),
                validate_roles=False,
            )

        return await self.build_identity(
            user_id=TEST_USER_OID,
            name=TEST_USER_NAME,
            email=TEST_USER_EMAIL,
            request=request,
        )

    @staticmethod
    def _seed_test_role(tenant_id: str) -> None:
        """Ensures the role the test identity claims actually grants something.

        Seeding only the user-to-role assignment left the role itself undefined, so
        `get_access_rules_for_roles` returned an empty set and every endpoint answered 403. pytest
        concealed it by mocking the role lookup; interactively the server authenticated fine and then
        refused every request. The name is deliberately unmistakable in a role list.
        """
        if RoleEntity.objects(name=TEST_USER_ROLE_NAME, tenant_id=tenant_id).first():
            return

        RoleEntity.create_tenant_role(
            name=TEST_USER_ROLE_NAME,
            description="Full access for the bypass-auth test handler. Never create this by hand.",
            access_rules=list(TEST_TENANT_ACCESS_RULES),
            tenant_id=tenant_id,
        )

    @staticmethod
    async def resolve_tenant_for_user(request: Request, user_id: str) -> TenantIdentity:
        """Resolves the tenant from MongoDB, never from Keycloak.

        `TEST_USER_OID` is a MongoDB ObjectId, so it can never name a Keycloak user — the production
        pipeline's `get_user` call always 404s and every tenant-scoped request became a 500. pytest hid
        it by mocking `KeycloakAdminService`; an interactive playground server against a real Keycloak
        had no such mock and was simply unusable.

        Resolving from Mongo is also the more honest bypass: this handler already fabricates the
        identity, so consulting the identity provider about it was never going to mean anything.
        """
        requested = (request.path_params.get("tenant_id") or "").strip()
        if requested and requested != AuthHandler.ACTIVE_TENANT_SLUG:
            tenant = TenantMetadataEntity.objects(id=requested).first()
            if tenant:
                return TenantIdentity.from_tenant_metadata_entity(tenant)
        return await TestAuthHandler.get_active_tenant_for_user(user_id)

    @staticmethod
    async def get_active_tenant_for_user(user_id: str) -> TenantIdentity:
        """The startup tenant stands in for the active one, which Keycloak would otherwise own."""
        tenant = TenantMetadataEntity.get_startup_tenant_metadata()
        if not tenant:
            raise HTTPException(status_code=400, detail="No startup tenant exists to act within")
        return TenantIdentity.from_tenant_metadata_entity(tenant)

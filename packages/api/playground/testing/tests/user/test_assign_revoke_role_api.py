from unittest.mock import patch

import pytest
import pytest_asyncio
from asgi_lifespan import LifespanManager
from httpx import ASGITransport, AsyncClient
from mongoengine import connect, disconnect
from swiss_ai_hub.core.auth.keycloak.keycloak_admin_service import KeycloakAdminService
from swiss_ai_hub.core.infrastructure import AIHubSettings, MongoSettings
from swiss_ai_hub.core.persistence.access.entities.role_entity import RoleEntity
from swiss_ai_hub.core.persistence.access.entities.user_tenant_role_entity import UserTenantRoleEntity
from swiss_ai_hub.core.testing.auth_utils import TEST_TENANT_ID, TEST_USER_OID, TestAuthHandler

from swiss_ai_hub.api.routes.user.user_controller import UserController
from swiss_ai_hub.api.runners.api_test_runner import ApiTestRunner

BASE_URL = "http://test"
TENANT_URL = f"/api/v1/{TEST_TENANT_ID}/users"
ASSIGNABLE_ROLE = "Editor"
UNKNOWN_ROLE = "DefinitelyNotARealRole"
# A different OID so the conftest's "admin is a member of the tenant" mock
# can stay in place while we test the "target user is not in tenant" branch.
OTHER_USER_OID = "ffffffffffffffffffffffff"


@pytest.fixture(scope="function")
def mongo_db():
    connect(
        db=AIHubSettings().MONGO_MAIN_DB_NAME,
        host=MongoSettings().CONNECTION_STRING.get_secret_value(),
        uuidRepresentation="standard",
    )
    yield
    UserTenantRoleEntity.objects(user_id=TEST_USER_OID, tenant_id=TEST_TENANT_ID).delete()
    RoleEntity.objects(tenant_id=TEST_TENANT_ID, name=ASSIGNABLE_ROLE).delete()
    disconnect()


@pytest.fixture(scope="function")
def existing_role(mongo_db):
    """Seed a tenant-scoped role the tests can assign / revoke."""
    role = RoleEntity(
        name=ASSIGNABLE_ROLE,
        description="Test role for assign/revoke",
        access_rules=["aihub.user.>"],
        tenant_id=TEST_TENANT_ID,
    )
    role.save()
    yield role


@pytest.fixture(scope="function")
def member_of_tenant(mongo_db):
    """Seed a UserTenantRoleEntity row so KeycloakAdminService treats the user as a tenant member."""
    UserTenantRoleEntity.create_or_update(
        user_id=TEST_USER_OID,
        tenant_id=TEST_TENANT_ID,
        roles=[],
        validate_roles=False,
    )
    yield


@pytest_asyncio.fixture(scope="function")
async def api_client():
    runner = ApiTestRunner()
    auth = TestAuthHandler()
    runner.mount(UserController(auth=auth).assign_role().revoke_role())
    app = runner.create_app()
    async with LifespanManager(app) as lifespan:
        async with AsyncClient(transport=ASGITransport(app=lifespan.app), base_url=BASE_URL) as client:
            yield client


@pytest.mark.asyncio
async def test_assign_role_happy_path(api_client, member_of_tenant, existing_role):
    response = await api_client.post(
        f"{TENANT_URL}/{TEST_USER_OID}/roles",
        json={"role_name": ASSIGNABLE_ROLE},
    )
    assert response.status_code == 201
    assert ASSIGNABLE_ROLE in response.json()


@pytest.mark.asyncio
async def test_assign_role_is_idempotent(api_client, member_of_tenant, existing_role):
    first = await api_client.post(
        f"{TENANT_URL}/{TEST_USER_OID}/roles",
        json={"role_name": ASSIGNABLE_ROLE},
    )
    second = await api_client.post(
        f"{TENANT_URL}/{TEST_USER_OID}/roles",
        json={"role_name": ASSIGNABLE_ROLE},
    )
    assert first.status_code == 201
    assert second.status_code == 201
    assert second.json().count(ASSIGNABLE_ROLE) == 1


@pytest.mark.asyncio
async def test_assign_role_404_when_user_not_in_tenant(api_client, existing_role):
    # Admin (TEST_USER_OID) stays a tenant member so auth passes; target user does not.
    async def member_only_for_admin(user_id: str, tenant_id: str) -> bool:
        return user_id == TEST_USER_OID

    with patch.object(KeycloakAdminService, "is_user_member_of_tenant", side_effect=member_only_for_admin):
        response = await api_client.post(
            f"{TENANT_URL}/{OTHER_USER_OID}/roles",
            json={"role_name": ASSIGNABLE_ROLE},
        )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_assign_role_400_when_role_does_not_exist(api_client, member_of_tenant):
    response = await api_client.post(
        f"{TENANT_URL}/{TEST_USER_OID}/roles",
        json={"role_name": UNKNOWN_ROLE},
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_revoke_role_happy_path(api_client, member_of_tenant, existing_role):
    UserTenantRoleEntity.add_roles(
        user_id=TEST_USER_OID,
        tenant_id=TEST_TENANT_ID,
        roles_to_add=[ASSIGNABLE_ROLE],
    )

    response = await api_client.delete(f"{TENANT_URL}/{TEST_USER_OID}/roles/{ASSIGNABLE_ROLE}")

    assert response.status_code == 200
    assert ASSIGNABLE_ROLE not in response.json()


@pytest.mark.asyncio
async def test_revoke_role_is_idempotent(api_client, member_of_tenant):
    response = await api_client.delete(f"{TENANT_URL}/{TEST_USER_OID}/roles/{ASSIGNABLE_ROLE}")
    assert response.status_code == 200
    assert ASSIGNABLE_ROLE not in response.json()


@pytest.mark.asyncio
async def test_revoke_role_404_when_user_not_in_tenant(api_client):
    async def member_only_for_admin(user_id: str, tenant_id: str) -> bool:
        return user_id == TEST_USER_OID

    with patch.object(KeycloakAdminService, "is_user_member_of_tenant", side_effect=member_only_for_admin):
        response = await api_client.delete(f"{TENANT_URL}/{OTHER_USER_OID}/roles/{ASSIGNABLE_ROLE}")
    assert response.status_code == 404

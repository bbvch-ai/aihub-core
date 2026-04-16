import os
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import pytest
import pytest_asyncio
from asgi_lifespan import LifespanManager
from httpx import ASGITransport, AsyncClient
from mongoengine import connect, disconnect
from swiss_ai_hub.core.auth.dependencies.token_auth_handler.token_auth_handler import TokenAuthHandler
from swiss_ai_hub.core.infrastructure import AIHubSettings, MongoSettings
from swiss_ai_hub.core.persistence.access.entities.bearer_token import BearerToken
from swiss_ai_hub.core.persistence.access.entities.role_entity import RoleEntity
from swiss_ai_hub.core.persistence.access.entities.tenant_metadata_entity import TenantMetadataEntity
from swiss_ai_hub.core.persistence.access.entities.user_tenant_role_entity import UserTenantRoleEntity
from swiss_ai_hub.core.testing.auth_utils import TEST_USER_EMAIL, TEST_USER_NAME, TEST_USER_OID, TEST_USER_ROLES

from swiss_ai_hub.api.routes.my_account.my_account_controller import MyAccountController
from swiss_ai_hub.api.runners.api_test_runner import ApiTestRunner

BASE_URL = "http://test"
USER_ENDPOINT = "/api/v1/active/my-account"
EXPECTED_USER_FIELDS = ["id", "name", "email", "roles", "profile_image"]


@pytest.fixture
def mongo_db():
    """Set up and tear down the MongoDB connection for tests."""
    connect(
        db=AIHubSettings().MONGO_MAIN_DB_NAME,
        host=MongoSettings().CONNECTION_STRING.get_secret_value(),
        uuidRepresentation="standard",
    )
    yield
    disconnect()


@pytest.fixture
def valid_token(mongo_db):
    """Insert a valid token document and return its token string."""
    config = SimpleNamespace(OID=TEST_USER_OID, NAME=TEST_USER_NAME, EMAIL=TEST_USER_EMAIL, ROLES=TEST_USER_ROLES)
    user_oid = os.getenv("OID", config.OID)

    # Create the test role on the default tenant so AccessChecker can resolve access rules
    default_tenant = TenantMetadataEntity.get_default_tenant_metadata()
    role: RoleEntity | None = None
    created_role = False
    if default_tenant:
        tenant_id = str(default_tenant.id)
        # Reuse the role if a prior test run left it behind; only track `created_role`
        # when we actually insert so teardown doesn't delete rows we didn't create.
        role = RoleEntity.objects(name=config.ROLES[0], tenant_id=tenant_id).first()
        if not role:
            role = RoleEntity.create_tenant_role(
                name=config.ROLES[0],
                description="Full admin access for testing",
                access_rules=["aihub.admin.>"],
                tenant_id=tenant_id,
            )
            created_role = True

    # Assign roles to user in default tenant (required for multi-tenant auth)
    user_tenant_role = None
    if default_tenant:
        user_tenant_role = UserTenantRoleEntity.create_or_update(
            user_id=user_oid,
            tenant_id=str(default_tenant.id),
            roles=config.ROLES,
            validate_roles=False,
        )

    expiry = datetime.now(UTC) + timedelta(hours=1)
    token_obj = BearerToken.create_new_token(name="token-name", expiry_date=expiry, user_oid=user_oid)
    yield token_obj.token
    token_obj.delete()
    if user_tenant_role:
        user_tenant_role.delete()
    if created_role:
        role.delete()


@pytest.fixture
def expected_user_data():
    """Return the expected user data based on environment variables."""
    return {
        "id": os.getenv("OID", TEST_USER_OID),
        "name": os.getenv("NAME", TEST_USER_NAME),
        "email": os.getenv("EMAIL", TEST_USER_EMAIL),
        "profile_image": None,
        "roles": TEST_USER_ROLES,
        "is_sys_admin": False,
    }


@pytest_asyncio.fixture(scope="module")
async def token_api_client():
    """Create a TestClient with MyAccountController mounted using TokenAuthHandler."""
    runner = ApiTestRunner()
    auth = TokenAuthHandler()
    runner.mount(MyAccountController(auth=auth).get_my_account())
    app = runner.create_app()
    async with LifespanManager(app) as lifespan:
        async with AsyncClient(transport=ASGITransport(app=lifespan.app), base_url=BASE_URL) as client:
            yield client


@pytest.mark.asyncio
async def test_get_user_with_valid_token(token_api_client, valid_token, expected_user_data):
    """Test GET /my-account with a valid token returns expected user data."""
    headers = {
        "Authorization": f"Bearer {valid_token}",
        "Content-Type": "application/json",
    }
    response = await token_api_client.get(USER_ENDPOINT, headers=headers)
    assert response.status_code == 200, f"Expected 200 but got {response.status_code}: {response.text}"
    user_data = response.json()

    # These fields are tested in other tests
    del user_data["dashboard"]
    del user_data["access"]

    assert all(key in user_data for key in EXPECTED_USER_FIELDS)
    assert user_data == expected_user_data


@pytest.mark.asyncio
async def test_get_user_with_invalid_token(token_api_client):
    """Test GET /my-account with an invalid token returns 401 or 403."""
    headers = {
        "Authorization": "Bearer invalid.token.value",
        "Content-Type": "application/json",
    }
    response = await token_api_client.get(USER_ENDPOINT, headers=headers)
    assert response.status_code in (
        401,
        403,
    ), f"Expected 401/403 for invalid token but got {response.status_code}: {response.text}"

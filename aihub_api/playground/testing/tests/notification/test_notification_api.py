import pytest
import pytest_asyncio
from aihub_lib.auth.dependencies.DangerousDevelopmentOnlyAuthHandler.DangerousDevelopmentOnlyAuthHandler import (
    DangerousDevelopmentOnlyAuthHandler,
)
from aihub_lib.auth.identity.DangerousDevelopmentOnlyIdentityProvider.DangerousDevelopmentOnlyIdentityProvider import (
    DangerousDevelopmentOnlyIdentityProvider,
)
from aihub_lib.infrastructure.ApiConfig import ApiConfig
from aihub_lib.infrastructure.azure.cosmos.CosmosAccess import CosmosAccess
from aihub_lib.persistence.notification.NotificationEntity import NotificationEntity
from aihub_lib.testing.auth_utils.user_mocks import mock_user_entity_autouse  # noqa: F401
from asgi_lifespan import LifespanManager
from httpx import ASGITransport, AsyncClient
from mongoengine import connect, disconnect

from aihub_api.routes.notification.NotificationController import NotificationController
from aihub_api.runners.ApiTestRunner import ApiTestRunner

BASE_URL = "http://test"
NOTIFICATIONS_ENDPOINT = "/api/v1/notifications"


@pytest.fixture(scope="module", autouse=True)
def mongo_db():
    """Set up and tear down the MongoDB connection for tests."""
    connect(db=ApiConfig().DB_NAME, host=CosmosAccess().get_connection_string())
    # Clean up before running tests
    NotificationEntity.objects.delete()
    yield
    # Clean up after tests
    NotificationEntity.objects.delete()
    disconnect()


@pytest_asyncio.fixture(scope="module")
async def api_client():
    """Create a test client for the API with NotificationController mounted."""
    runner = ApiTestRunner()
    auth = DangerousDevelopmentOnlyAuthHandler(identity_provider=DangerousDevelopmentOnlyIdentityProvider())
    runner.mount(NotificationController(auth=auth).get_notifications().mark_as_read())
    app = runner.get_app()
    async with LifespanManager(app) as lifespan:
        async with AsyncClient(transport=ASGITransport(app=lifespan.app), base_url=BASE_URL) as client:
            yield client


@pytest.mark.asyncio
async def test_get_notifications(api_client: AsyncClient):
    """Test GET /notifications returns a list of notifications."""
    response = await api_client.get(NOTIFICATIONS_ENDPOINT)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    # Mock data creates 3 notifications
    assert len(data) == 3
    assert "title" in data[0]
    assert data[0]["read"] is False
    assert data[1]["read"] is True


@pytest.mark.asyncio
async def test_mark_notification_as_read(api_client: AsyncClient):
    """Test POST /notifications/{id}/read marks a notification as read."""
    # First, get notifications to find an unread one
    get_response = await api_client.get(NOTIFICATIONS_ENDPOINT)
    notifications = get_response.json()
    unread_notification = next((n for n in notifications if not n["read"]), None)
    assert unread_notification is not None, "No unread notification found to test with"

    # Mark it as read
    notification_id = unread_notification["id"]
    post_response = await api_client.post(f"{NOTIFICATIONS_ENDPOINT}/{notification_id}/read")
    assert post_response.status_code == 200
    updated_notification = post_response.json()
    assert updated_notification["id"] == notification_id
    assert updated_notification["read"] is True

    # Verify it's marked as read in the main list
    get_again_response = await api_client.get(NOTIFICATIONS_ENDPOINT)
    notifications_after_read = get_again_response.json()
    notification_in_list = next((n for n in notifications_after_read if n["id"] == notification_id), None)
    assert notification_in_list is not None
    assert notification_in_list["read"] is True


@pytest.mark.asyncio
async def test_mark_nonexistent_notification_as_read(api_client: AsyncClient):
    """Test marking a non-existent notification returns 404."""
    non_existent_id = "60c72b2f9b1e8b001f8e4c3d"  # Example of a valid but non-existent ObjectId
    post_response = await api_client.post(f"{NOTIFICATIONS_ENDPOINT}/{non_existent_id}/read")
    assert post_response.status_code == 404
    assert post_response.json()["detail"] == "Notification not found."

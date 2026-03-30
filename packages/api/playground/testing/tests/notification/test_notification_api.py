from datetime import datetime
from unittest.mock import patch

import pytest
import pytest_asyncio
from asgi_lifespan import LifespanManager
from httpx import ASGITransport, AsyncClient
from mongoengine import connect, disconnect
from swiss_ai_hub.core.auth.dependencies.dangerous_development_only_auth_handler.dangerous_development_only_auth_handler import (  # noqa: E501
    DangerousDevelopmentOnlyAuthHandler,
)
from swiss_ai_hub.core.infrastructure import AIHubSettings, MongoSettings

from swiss_ai_hub.api.routes.notification.dto.notification_dto import NotificationDTO
from swiss_ai_hub.api.routes.notification.dto.paginated_notifications_response import PaginatedNotificationsResponse
from swiss_ai_hub.api.routes.notification.notification_controller import NotificationController
from swiss_ai_hub.api.runners.api_test_runner import ApiTestRunner

BASE_URL = "http://test"
NOTIFICATIONS_ENDPOINT = "/api/v1/active/notifications"


@pytest.fixture(scope="module", autouse=True)
def mongo_db():
    """Set up and tear down the MongoDB connection for tests."""
    connect(
        db=AIHubSettings().MONGO_MAIN_DB_NAME,
        host=MongoSettings().CONNECTION_STRING.get_secret_value(),
        uuidRepresentation="standard",
    )
    yield
    disconnect()


@pytest_asyncio.fixture(scope="module")
async def api_client():
    """Create a test client for the API with NotificationController mounted."""
    runner = ApiTestRunner()
    auth = DangerousDevelopmentOnlyAuthHandler()
    controller = NotificationController(auth=auth)
    controller.get_notifications().update_notification().update_notifications()
    runner.mount(controller)
    app = runner.create_app()
    async with LifespanManager(app) as lifespan:
        async with AsyncClient(transport=ASGITransport(app=lifespan.app), base_url=BASE_URL) as client:
            yield client


@pytest.fixture
def mock_notification_dto():
    """Create a mock NotificationDTO for testing."""
    return NotificationDTO(
        id="507f1f77bcf86cd799439011",  # Valid ObjectId
        user_id="507f1f77bcf86cd799439012",  # Valid ObjectId
        notification_group_id="507f1f77bcf86cd799439013",  # Valid ObjectId
        title="Test Notification",
        message="This is a test notification message",
        read=False,
        done=False,
        type="info",
        severity="medium",
        link="/test-link",
        created_at=datetime.now(),
    )


@pytest.fixture
def mock_paginated_response(mock_notification_dto):
    """Create a mock PaginatedNotificationsResponse for testing."""
    return PaginatedNotificationsResponse(
        notifications=[mock_notification_dto],
        total=1,  # Changed from total_count to total
        page=1,
        page_size=20,
        total_pages=1,
    )


class TestGetNotifications:
    """Test suite for GET /notifications endpoint."""

    @pytest.mark.asyncio
    async def test_get_notifications_success(self, api_client, mock_paginated_response):
        """Test successful retrieval of notifications."""
        with patch(
            "swiss_ai_hub.api.routes.notification.notification_service.NotificationService.get_notifications_for_user"
        ) as mock_service:
            mock_service.return_value = mock_paginated_response

            response = await api_client.get(NOTIFICATIONS_ENDPOINT)

            assert response.status_code == 200
            data = response.json()
            assert "notifications" in data
            assert "total" in data
            assert "page" in data
            assert "page_size" in data
            assert "total_pages" in data
            assert isinstance(data["notifications"], list)

    @pytest.mark.asyncio
    async def test_get_notifications_with_pagination(self, api_client, mock_paginated_response):
        """Test notifications endpoint with pagination parameters."""
        with patch(
            "swiss_ai_hub.api.routes.notification.notification_service.NotificationService.get_notifications_for_user"
        ) as mock_service:
            mock_service.return_value = mock_paginated_response

            response = await api_client.get(f"{NOTIFICATIONS_ENDPOINT}?page=2&page_size=10")

            assert response.status_code == 200
            mock_service.assert_called_once()
            call_args = mock_service.call_args
            assert call_args[0][1] == 2  # page
            assert call_args[0][2] == 10  # page_size

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "filters,expected_filters",
        [
            ("types=info&types=error", {"types": ["info", "error"]}),
            ("severities=high&severities=critical", {"severities": ["high", "critical"]}),
            ("read=true", {"read": True}),
            ("done=false", {"done": False}),
            ("types=info&read=true&done=false", {"types": ["info"], "read": True, "done": False}),
        ],
    )
    async def test_get_notifications_with_filters(self, api_client, mock_paginated_response, filters, expected_filters):
        """Test notifications endpoint with various filters."""
        with patch(
            "swiss_ai_hub.api.routes.notification.notification_service.NotificationService.get_notifications_for_user"
        ) as mock_service:
            mock_service.return_value = mock_paginated_response

            response = await api_client.get(f"{NOTIFICATIONS_ENDPOINT}?{filters}")

            assert response.status_code == 200
            mock_service.assert_called_once()
            call_kwargs = mock_service.call_args[1]
            for key, value in expected_filters.items():
                assert call_kwargs[key] == value

    @pytest.mark.asyncio
    async def test_get_notifications_invalid_pagination(self, api_client):
        """Test notifications endpoint with invalid pagination parameters."""
        # Test page < 1
        response = await api_client.get(f"{NOTIFICATIONS_ENDPOINT}?page=0")
        assert response.status_code == 422

        # Test page_size > 100
        response = await api_client.get(f"{NOTIFICATIONS_ENDPOINT}?page_size=101")
        assert response.status_code == 422

        # Test page_size < 1
        response = await api_client.get(f"{NOTIFICATIONS_ENDPOINT}?page_size=0")
        assert response.status_code == 422


class TestUpdateNotification:
    """Test suite for PATCH /notifications/{notification_id} endpoint."""

    @pytest.mark.asyncio
    async def test_update_notification_success(self, api_client, mock_notification_dto):
        """Test successful update of a single notification."""
        with patch(
            "swiss_ai_hub.api.routes.notification.notification_service.NotificationService.update_one"
        ) as mock_service:
            mock_service.return_value = mock_notification_dto

            update_data = {"read": True, "done": False}
            response = await api_client.patch(f"{NOTIFICATIONS_ENDPOINT}/507f1f77bcf86cd799439011", json=update_data)

            assert response.status_code == 200
            data = response.json()
            assert data["id"] == "507f1f77bcf86cd799439011"
            mock_service.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_notification_not_found(self, api_client):
        """Test update notification when notification doesn't exist."""
        from mongoengine import DoesNotExist

        with patch(
            "swiss_ai_hub.api.routes.notification.notification_service.NotificationService.update_one"
        ) as mock_service:
            mock_service.side_effect = DoesNotExist()

            update_data = {"read": True}
            response = await api_client.patch(f"{NOTIFICATIONS_ENDPOINT}/507f1f77bcf86cd799439999", json=update_data)

            assert response.status_code == 404
            data = response.json()
            assert data["detail"] == "Notification not found."

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "update_data",
        [
            {"read": True},
            {"done": True},
            {"read": False, "done": True},
            {"read": True, "done": False},
        ],
    )
    async def test_update_notification_valid_fields(self, api_client, mock_notification_dto, update_data):
        """Test updating notification with valid field combinations."""
        with patch(
            "swiss_ai_hub.api.routes.notification.notification_service.NotificationService.update_one"
        ) as mock_service:
            mock_service.return_value = mock_notification_dto

            response = await api_client.patch(f"{NOTIFICATIONS_ENDPOINT}/507f1f77bcf86cd799439011", json=update_data)

            assert response.status_code == 200
            mock_service.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_notification_invalid_data(self, api_client):
        """Test update notification with invalid data (fields are ignored by Pydantic)."""
        with patch(
            "swiss_ai_hub.api.routes.notification.notification_service.NotificationService.update_one"
        ) as mock_service:
            from mongoengine import DoesNotExist

            mock_service.side_effect = DoesNotExist()

            invalid_data = {"invalid_field": "value"}
            response = await api_client.patch(f"{NOTIFICATIONS_ENDPOINT}/507f1f77bcf86cd799439011", json=invalid_data)

            # Invalid fields are ignored, but notification doesn't exist
            assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_notification_empty_body(self, api_client):
        """Test update notification with empty request body."""
        with patch(
            "swiss_ai_hub.api.routes.notification.notification_service.NotificationService.update_one"
        ) as mock_service:
            from mongoengine import DoesNotExist

            mock_service.side_effect = DoesNotExist()

            response = await api_client.patch(f"{NOTIFICATIONS_ENDPOINT}/507f1f77bcf86cd799439011", json={})

            # Empty body is valid but notification doesn't exist
            assert response.status_code == 404


class TestBulkUpdateNotifications:
    """Test suite for PATCH /notifications/ endpoint (bulk update)."""

    @pytest.mark.asyncio
    async def test_bulk_update_notifications_success(self, api_client, mock_notification_dto):
        """Test successful bulk update of notifications."""
        with patch(
            "swiss_ai_hub.api.routes.notification.notification_service.NotificationService.update_many"
        ) as mock_service:
            mock_service.return_value = [mock_notification_dto]

            bulk_update_data = {
                "notification_ids": ["507f1f77bcf86cd799439011", "507f1f77bcf86cd799439012"],
                "updates": {"read": True, "done": False},
            }
            response = await api_client.patch(f"{NOTIFICATIONS_ENDPOINT}/", json=bulk_update_data)

            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)
            assert len(data) == 1
            mock_service.assert_called_once()

    @pytest.mark.asyncio
    async def test_bulk_update_notifications_empty_ids(self, api_client):
        """Test bulk update with empty notification IDs list."""
        with patch(
            "swiss_ai_hub.api.routes.notification.notification_service.NotificationService.update_many"
        ) as mock_service:
            mock_service.return_value = []

            bulk_update_data = {"notification_ids": [], "updates": {"read": True}}
            response = await api_client.patch(f"{NOTIFICATIONS_ENDPOINT}/", json=bulk_update_data)

            # Empty list is valid, returns empty result
            assert response.status_code == 200
            data = response.json()
            assert data == []

    @pytest.mark.asyncio
    async def test_bulk_update_notifications_invalid_updates(self, api_client, mock_notification_dto):
        """Test bulk update with invalid update fields (ignored by Pydantic)."""
        with patch(
            "swiss_ai_hub.api.routes.notification.notification_service.NotificationService.update_many"
        ) as mock_service:
            mock_service.return_value = [mock_notification_dto]

            bulk_update_data = {"notification_ids": ["507f1f77bcf86cd799439011"], "updates": {"invalid_field": "value"}}
            response = await api_client.patch(f"{NOTIFICATIONS_ENDPOINT}/", json=bulk_update_data)

            # Invalid fields are ignored, request succeeds
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)
            assert len(data) == 1

    @pytest.mark.asyncio
    async def test_bulk_update_notifications_missing_fields(self, api_client):
        """Test bulk update with missing required fields."""
        # Missing notification_ids
        response = await api_client.patch(f"{NOTIFICATIONS_ENDPOINT}/", json={"updates": {"read": True}})
        assert response.status_code == 422

        # Missing updates
        response = await api_client.patch(
            f"{NOTIFICATIONS_ENDPOINT}/", json={"notification_ids": ["507f1f77bcf86cd799439011"]}
        )
        assert response.status_code == 422


class TestNotificationControllerIntegration:
    """Integration tests for the notification controller."""

    @pytest.mark.asyncio
    async def test_notification_dto_structure(self, api_client, mock_notification_dto):
        """Test that notification DTO has the expected structure."""
        with patch(
            "swiss_ai_hub.api.routes.notification.notification_service.NotificationService.update_one"
        ) as mock_service:
            mock_service.return_value = mock_notification_dto

            response = await api_client.patch(f"{NOTIFICATIONS_ENDPOINT}/507f1f77bcf86cd799439011", json={"read": True})

            data = response.json()
            expected_fields = [
                "id",
                "user_id",
                "notification_group_id",
                "title",
                "message",
                "read",
                "done",
                "type",
                "severity",
                "link",
                "created_at",
            ]
            assert all(field in data for field in expected_fields)
            assert isinstance(data["read"], bool)
            assert isinstance(data["done"], bool)
            assert data["type"] in ["success", "info", "warn", "error"]
            assert data["severity"] in ["low", "medium", "high", "critical"]

    @pytest.mark.asyncio
    async def test_content_type_handling(self, api_client):
        """Test that endpoints handle different content types correctly."""
        headers = {"Content-Type": "application/json"}
        response = await api_client.get(NOTIFICATIONS_ENDPOINT, headers=headers)
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_localization_handling(self, api_client, mock_paginated_response):
        """Test that endpoints handle localization correctly."""
        with patch(
            "swiss_ai_hub.api.routes.notification.notification_service.NotificationService.get_notifications_for_user"
        ) as mock_service:
            mock_service.return_value = mock_paginated_response

            headers = {"Accept-Language": "en-US"}
            response = await api_client.get(NOTIFICATIONS_ENDPOINT, headers=headers)

            assert response.status_code == 200
            # The locale handler should be called with the request
            mock_service.assert_called_once()

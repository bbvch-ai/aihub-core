from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aihub_lib.auth.dependencies.DangerousDevelopmentOnlyAuthHandler.DangerousDevelopmentOnlyAuthHandler import (
    DangerousDevelopmentOnlyAuthHandler,
)
from aihub_lib.auth.identity.DangerousDevelopmentOnlyIdentityProvider.DangerousDevelopmentOnlyIdentityProvider import (
    DangerousDevelopmentOnlyIdentityProvider,
)
from aihub_lib.auth.usage import UsageStatus
from aihub_lib.testing.auth_utils.role_mocks import mock_role_entity_admin_only  # noqa: F401
from asgi_lifespan import LifespanManager
from httpx import ASGITransport, AsyncClient

from aihub_api.routes.openai.OpenaiController import OpenaiController
from aihub_api.runners.ApiTestRunner import ApiTestRunner

BASE_URL = "http://test"
CHAT_ENDPOINT = "/api/v1/openai/chat/completions"


class TestUsageLimitEnforcement:
    """Tests for usage limit enforcement in OpenAI chat completions."""

    @pytest.mark.asyncio
    @patch("aihub_api.routes.openai.OpenaiController.UsageLimitService")
    async def test_returns_429_when_limit_exceeded(self, mock_usage_service: MagicMock):
        """Test that a 429 error is returned when usage limit is exceeded."""
        mock_usage_service.check_and_increment = AsyncMock(
            return_value=UsageStatus(
                current_count=101,
                limit=100,
                period="1d",
                reset_at=None,
                is_exceeded=True,
            )
        )

        auth = DangerousDevelopmentOnlyAuthHandler(identity_provider=DangerousDevelopmentOnlyIdentityProvider())
        controller = OpenaiController(auth=auth).chat_completion_with_assistants()
        runner = ApiTestRunner()
        runner.mount(controller)
        app = runner.create_app()

        async with LifespanManager(app) as lifespan:
            async with AsyncClient(transport=ASGITransport(app=lifespan.app), base_url=BASE_URL) as client:
                # Use an agent model format (has a single slash)
                payload = {
                    "model": "TestAgent/test_id",
                    "messages": [{"role": "user", "content": "Hello"}],
                    "stream": False,
                }
                response = await client.post(CHAT_ENDPOINT, json=payload)

                assert response.status_code == 429, f"Expected 429, got {response.status_code}: {response.text}"
                data = response.json()
                assert data["detail"]["error"] == "usage_limit_exceeded"
                assert data["detail"]["limit"] == 100
                assert data["detail"]["period"] == "1d"

    @pytest.mark.asyncio
    @patch("aihub_api.routes.openai.OpenaiController.UsageLimitService")
    async def test_direct_model_calls_not_counted(self, mock_usage_service: MagicMock):
        """Test that direct model calls (not agent calls) are not counted."""
        auth = DangerousDevelopmentOnlyAuthHandler(identity_provider=DangerousDevelopmentOnlyIdentityProvider())
        controller = OpenaiController(auth=auth).chat_completion_with_assistants()
        runner = ApiTestRunner()
        runner.mount(controller)
        app = runner.create_app()

        async with LifespanManager(app) as lifespan:
            async with AsyncClient(transport=ASGITransport(app=lifespan.app), base_url=BASE_URL) as client:
                # Use a direct model format (has two slashes: category/size)
                payload = {
                    "model": "text-generation/mini",
                    "messages": [{"role": "user", "content": "Hello"}],
                    "stream": False,
                }
                await client.post(CHAT_ENDPOINT, json=payload)

                # The actual response may succeed or fail depending on model availability,
                # but the key point is that check_and_increment should NOT be called
                mock_usage_service.check_and_increment.assert_not_called()

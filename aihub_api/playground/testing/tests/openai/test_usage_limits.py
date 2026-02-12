from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aihub_lib.auth.dependencies.DangerousDevelopmentOnlyAuthHandler.DangerousDevelopmentOnlyAuthHandler import (
    DangerousDevelopmentOnlyAuthHandler,
)
from aihub_lib.auth.identity.DangerousDevelopmentOnlyIdentityProvider.DangerousDevelopmentOnlyIdentityProvider import (
    DangerousDevelopmentOnlyIdentityProvider,
)
from aihub_lib.auth.usage import RoleUsageLimitStatus, UsageLimitPeriod, UsageStatus
from aihub_lib.testing.auth_utils.role_mocks import mock_role_entity_admin_only  # noqa: F401
from asgi_lifespan import LifespanManager
from fastapi import HTTPException
from httpx import ASGITransport, AsyncClient

from aihub_api.routes.openai.OpenaiController import OpenaiController
from aihub_api.runners.ApiTestRunner import ApiTestRunner

BASE_URL = "http://test"
CHAT_ENDPOINT = "/api/v1/openai/chat/completions"


def _exceeded_status(*, limit: int = 100, current_count: int = 101, period: str = "1d") -> UsageStatus:
    """Build a UsageStatus that is exceeded."""
    return UsageStatus(
        limits=[
            RoleUsageLimitStatus(
                pattern="aihub.user.agent.>",
                limit=limit,
                period=UsageLimitPeriod(period),
                current_count=current_count,
                reset_at=None,
                is_exceeded=True,
            )
        ],
        is_exceeded=True,
    )


def _mock_agent_dto() -> MagicMock:
    """Create a mock agent DTO that passes the is_conversational check."""
    dto = MagicMock()
    dto.is_conversational = True
    return dto


class TestUsageLimitEnforcement:
    """Tests for usage limit enforcement in OpenAI chat completions."""

    @pytest.mark.asyncio
    @patch("aihub_api.routes.openai.OpenaiService.AgentService.get_agent", new_callable=AsyncMock)
    @patch("aihub_api.routes.openai.OpenaiService.UsageLimits.check_and_raise", new_callable=AsyncMock)
    async def test_returns_429_when_limit_exceeded(self, mock_check_usage: AsyncMock, mock_get_agent: AsyncMock):
        """Test that a 429 error is returned when usage limit is exceeded."""
        from aihub_lib.auth.usage.UsageLimitMessages import UsageLimitMessages

        build_exceeded_detail = UsageLimitMessages.build_exceeded_detail

        exceeded = _exceeded_status()
        mock_get_agent.return_value = _mock_agent_dto()
        mock_check_usage.side_effect = HTTPException(
            status_code=429, detail=build_exceeded_detail(exceeded, locale="en").model_dump()
        )

        auth = DangerousDevelopmentOnlyAuthHandler(identity_provider=DangerousDevelopmentOnlyIdentityProvider())
        controller = OpenaiController(auth=auth).chat_completion_with_assistants()
        runner = ApiTestRunner()
        runner.mount(controller)
        app = runner.create_app()

        async with LifespanManager(app) as lifespan:
            async with AsyncClient(transport=ASGITransport(app=lifespan.app), base_url=BASE_URL) as client:
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
                assert data["detail"]["period"] == UsageLimitPeriod.ONE_DAY

    @pytest.mark.asyncio
    @patch("aihub_api.routes.openai.OpenaiService.UsageLimits.check_and_raise", new_callable=AsyncMock)
    async def test_direct_model_calls_not_counted(self, mock_check_usage: AsyncMock):
        """Test that direct model calls (not agent calls) are not counted."""
        auth = DangerousDevelopmentOnlyAuthHandler(identity_provider=DangerousDevelopmentOnlyIdentityProvider())
        controller = OpenaiController(auth=auth).chat_completion_with_assistants()
        runner = ApiTestRunner()
        runner.mount(controller)
        app = runner.create_app()

        async with LifespanManager(app) as lifespan:
            async with AsyncClient(transport=ASGITransport(app=lifespan.app), base_url=BASE_URL) as client:
                payload = {
                    "model": "text-generation/mini",
                    "messages": [{"role": "user", "content": "Hello"}],
                    "stream": False,
                }
                await client.post(CHAT_ENDPOINT, json=payload)

                # Direct model calls don't go through ChatService, so check_and_raise should not be called
                mock_check_usage.assert_not_called()

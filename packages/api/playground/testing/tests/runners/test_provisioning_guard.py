import logging
from unittest.mock import AsyncMock

import pytest

from swiss_ai_hub.api.runners.lifetime.lifetime_manager import _provision_non_fatal


class TestProvisionNonFatal:
    @pytest.mark.asyncio
    async def test_failure_is_swallowed_and_logged(self, caplog: pytest.LogCaptureFixture) -> None:
        provision = AsyncMock(side_effect=RuntimeError("boom"))

        with caplog.at_level(logging.ERROR):
            await _provision_non_fatal("OpenWebUI", provision)

        assert "OpenWebUI provisioning failed (non-fatal)" in caplog.text
        assert "boom" in caplog.text

    @pytest.mark.asyncio
    async def test_success_awaits_provisioner_without_logging(self, caplog: pytest.LogCaptureFixture) -> None:
        provision = AsyncMock()

        with caplog.at_level(logging.ERROR):
            await _provision_non_fatal("Langfuse", provision)

        provision.assert_awaited_once()
        assert not caplog.records

"""Tests for AccessChangeHook debouncing."""

import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from swiss_ai_hub.core.persistence.access.access_change_hook import AccessChangeHook


@pytest.fixture(autouse=True)
def _reset_hook() -> None:
    AccessChangeHook._debounce_task = None


class TestDebounce:
    @pytest.mark.asyncio
    async def test_rapid_schedule_sync_calls_result_in_single_sync(self) -> None:
        mock_sync = AsyncMock()
        mock_provisioner = AsyncMock()
        mock_provisioner.sync_access = mock_sync
        with patch(
            "swiss_ai_hub.core.persistence.access.access_change_hook.OpenWebuiProvisioner",
            return_value=mock_provisioner,
        ):
            AccessChangeHook._schedule_sync()
            AccessChangeHook._schedule_sync()
            AccessChangeHook._schedule_sync()

            await asyncio.sleep(2.5)

            assert mock_sync.call_count == 1

    @pytest.mark.asyncio
    async def test_schedule_sync_cancels_previous_task(self) -> None:
        AccessChangeHook._schedule_sync()
        first_task = AccessChangeHook._debounce_task

        AccessChangeHook._schedule_sync()
        second_task = AccessChangeHook._debounce_task

        assert first_task is not second_task
        await asyncio.sleep(0)
        assert first_task.cancelled()

        second_task.cancel()

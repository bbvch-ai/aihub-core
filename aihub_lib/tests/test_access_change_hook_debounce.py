"""Tests for AccessChangeHook debouncing."""

import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from aihub_lib.infrastructure.openwebui.OpenWebuiProvisioner import OpenWebuiProvisioner
from aihub_lib.persistence.access.AccessChangeHook import AccessChangeHook


@pytest.fixture(autouse=True)
def _reset_hook() -> None:
    AccessChangeHook._debounce_task = None


class TestDebounce:
    @pytest.mark.asyncio
    async def test_rapid_schedule_sync_calls_result_in_single_sync(self) -> None:
        with patch.object(OpenWebuiProvisioner, "sync_access", new_callable=AsyncMock) as mock_sync:
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

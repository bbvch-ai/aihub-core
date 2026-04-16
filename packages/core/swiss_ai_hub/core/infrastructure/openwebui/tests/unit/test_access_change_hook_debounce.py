import asyncio

import pytest

from swiss_ai_hub.core.persistence.access.access_change_hook import AccessChangeHook
from swiss_ai_hub.core.testing.auth_utils.user_mocks import mock_keycloak_admin_service_autouse  # noqa: F401


class TestDebounce:
    @pytest.mark.asyncio
    async def test_multiple_schedules_result_in_single_sync(self):
        call_count = 0

        async def mock_sync_access():
            nonlocal call_count
            call_count += 1

        original_debounced = AccessChangeHook._debounced_sync

        async def patched_debounced():
            await asyncio.sleep(0.1)
            await mock_sync_access()

        AccessChangeHook._debounced_sync = classmethod(lambda cls: patched_debounced())

        try:
            AccessChangeHook._schedule_sync()
            AccessChangeHook._schedule_sync()
            AccessChangeHook._schedule_sync()

            await asyncio.sleep(0.3)

            assert call_count == 1
        finally:
            AccessChangeHook._debounced_sync = original_debounced
            AccessChangeHook._debounce_task = None

    @pytest.mark.asyncio
    async def test_schedule_cancels_previous_task(self):
        AccessChangeHook._debounce_task = None

        async def slow_sync():
            await asyncio.sleep(10)

        AccessChangeHook._debounced_sync = classmethod(lambda cls: slow_sync())

        try:
            AccessChangeHook._schedule_sync()
            first_task = AccessChangeHook._debounce_task

            AccessChangeHook._schedule_sync()
            second_task = AccessChangeHook._debounce_task

            # Yield control so cancellation propagates
            await asyncio.sleep(0)

            assert first_task.cancelled()
            assert not second_task.cancelled()

            second_task.cancel()
        finally:
            AccessChangeHook._debounce_task = None

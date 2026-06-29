import asyncio
import gc

import pytest
from mongoengine import signals

from swiss_ai_hub.core.persistence.access.access_change_hook import AccessChangeHook
from swiss_ai_hub.core.persistence.access.entities.role_entity import RoleEntity
from swiss_ai_hub.core.persistence.access.entities.tenant_metadata_entity import TenantMetadataEntity
from swiss_ai_hub.core.persistence.access.entities.user_tenant_role_entity import UserTenantRoleEntity

_WATCHED_ENTITIES = [RoleEntity, TenantMetadataEntity, UserTenantRoleEntity]


class TestSignalSubscriptionSurvives:
    """Regression for the weak-ref GC bug: ``connect`` wired a local closure with blinker's
    default weak reference, so it was garbage-collected the instant ``connect`` returned and no
    access change ever triggered a sync. The debounce tests below never caught this because they
    call ``_schedule_sync`` directly, bypassing the signal connection."""

    def test_connect_subscription_survives_gc(self):
        was_connected = AccessChangeHook._connected
        AccessChangeHook._connected = False

        class _DummyProvisioner:
            async def sync_access(self) -> None: ...

        try:
            AccessChangeHook.connect(_DummyProvisioner())
            gc.collect()  # a weakly-referenced local closure would be collected here

            for entity in _WATCHED_ENTITIES:
                assert list(signals.post_save.receivers_for(entity)), (
                    f"post_save receiver for {entity.__name__} was dropped — connect must use weak=False"
                )
                assert list(signals.post_delete.receivers_for(entity)), (
                    f"post_delete receiver for {entity.__name__} was dropped — connect must use weak=False"
                )
        finally:
            for sig in (signals.post_save, signals.post_delete):
                for entity in _WATCHED_ENTITIES:
                    for receiver in list(sig.receivers_for(entity)):
                        sig.disconnect(receiver, sender=entity)
            AccessChangeHook._connected = was_connected
            AccessChangeHook._provisioner = None


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

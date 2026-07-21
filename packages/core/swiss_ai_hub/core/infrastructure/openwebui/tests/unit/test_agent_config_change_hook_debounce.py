import asyncio
import gc

import pytest
from mongoengine import signals

from swiss_ai_hub.core.persistence.agents.agent_config_change_hook import AgentConfigChangeHook
from swiss_ai_hub.core.persistence.agents.agent_config_entity_document import AgentConfigEntityDocument


class TestSignalSubscriptionSurvives:
    """Regression for the weak-ref GC bug: a locally-defined closure wired with blinker's default
    weak reference is collected the instant ``connect`` returns, silently dropping the subscription
    so no config change ever triggers an OpenWebUI re-sync."""

    def test_connect_subscription_survives_gc(self):
        was_connected = AgentConfigChangeHook._connected
        AgentConfigChangeHook._connected = False

        class _DummyProvisioner:
            async def sync_known_agents(self) -> None:
                pass

        try:
            AgentConfigChangeHook.connect(_DummyProvisioner())
            gc.collect()  # a weakly-referenced local closure would be collected here

            assert list(signals.post_save.receivers_for(AgentConfigEntityDocument)), (
                "post_save receiver was dropped — connect must use weak=False"
            )
            assert list(signals.post_delete.receivers_for(AgentConfigEntityDocument)), (
                "post_delete receiver was dropped — connect must use weak=False"
            )
        finally:
            for sig in (signals.post_save, signals.post_delete):
                for receiver in list(sig.receivers_for(AgentConfigEntityDocument)):
                    sig.disconnect(receiver, sender=AgentConfigEntityDocument)
            AgentConfigChangeHook._connected = was_connected
            AgentConfigChangeHook._provisioner = None


class TestDebounce:
    @pytest.mark.asyncio
    async def test_multiple_schedules_result_in_single_sync(self):
        call_count = 0

        async def mock_sync():
            nonlocal call_count
            call_count += 1

        original_debounced = AgentConfigChangeHook._debounced_sync

        async def patched_debounced():
            await asyncio.sleep(0.1)
            await mock_sync()

        AgentConfigChangeHook._debounced_sync = classmethod(lambda cls: patched_debounced())

        try:
            AgentConfigChangeHook._schedule_sync()
            AgentConfigChangeHook._schedule_sync()
            AgentConfigChangeHook._schedule_sync()

            await asyncio.sleep(0.3)

            assert call_count == 1
        finally:
            AgentConfigChangeHook._debounced_sync = original_debounced
            AgentConfigChangeHook._debounce_task = None

    @pytest.mark.asyncio
    async def test_schedule_cancels_previous_task(self):
        AgentConfigChangeHook._debounce_task = None

        async def slow_sync():
            await asyncio.sleep(10)

        AgentConfigChangeHook._debounced_sync = classmethod(lambda cls: slow_sync())

        try:
            AgentConfigChangeHook._schedule_sync()
            first_task = AgentConfigChangeHook._debounce_task

            AgentConfigChangeHook._schedule_sync()
            second_task = AgentConfigChangeHook._debounce_task

            # Yield control so cancellation propagates
            await asyncio.sleep(0)

            assert first_task.cancelled()
            assert not second_task.cancelled()

            second_task.cancel()
        finally:
            AgentConfigChangeHook._debounce_task = None

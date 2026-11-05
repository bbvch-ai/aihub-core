import asyncio

import pytest

from swiss_ai_hub.core.i18n.locale_string import LocaleString
from swiss_ai_hub.core.persistence.agents import agent_config_change_hook
from swiss_ai_hub.core.persistence.agents.agent_config_change_hook import AgentConfigChangeHook
from swiss_ai_hub.core.persistence.agents.agent_config_entity_document import AgentConfigEntityDocument


class TestAProfileWriteReachesTheSync:
    """Beanie has no global signals, so the document itself notifies the hook; without that, OpenWebUI
    would silently stop reflecting created, renamed and deleted agents until the next discovery cycle."""

    @pytest.mark.beanie
    async def test_saving_a_profile_syncs_openwebui_once(self, monkeypatch: pytest.MonkeyPatch):
        synced: list[bool] = []

        class _RecordingProvisioner:
            async def sync_known_agents(self) -> None:
                synced.append(True)

        monkeypatch.setattr(agent_config_change_hook, "_DEBOUNCE_SECONDS", 0)
        monkeypatch.setattr(AgentConfigChangeHook, "_connected", False)
        monkeypatch.setattr(AgentConfigChangeHook, "_debounce_task", None)
        AgentConfigChangeHook.connect(_RecordingProvisioner())
        try:
            await AgentConfigEntityDocument(
                agent_class="RAGAgent",
                agent_id="hr",
                name=LocaleString(en="HR"),
                description=LocaleString(en="HR profile"),
                icon="meteor-icons:robot",
                config_data={},
            ).insert()
            await AgentConfigChangeHook._debounce_task
        finally:
            AgentConfigChangeHook._provisioner = None

        assert synced == [True]


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

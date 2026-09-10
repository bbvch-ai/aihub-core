from unittest.mock import AsyncMock, patch

import httpx
import pytest

from swiss_ai_hub.core.infrastructure.openwebui.online_agent import OnlineAgent
from swiss_ai_hub.core.infrastructure.openwebui.openwebui_provisioner import (
    AIHUB_MANAGED_META_KEY,
    OpenWebuiProvisioner,
)
from swiss_ai_hub.core.persistence.i18n.locale_string_entity import LocaleStringEntity

_RAG_AGENT = OnlineAgent(agent_class="rag", agent_id="default", display_name="RAG Agent")


class TestResolveDisplayName:
    def test_uses_configured_locale(self, provisioner: OpenWebuiProvisioner) -> None:
        provisioner._settings.MODEL_NAME_LOCALE = "en"
        name = LocaleStringEntity(de="Such-Agent", en="Search Agent", fr="Agent", it="Agente")

        assert provisioner._resolve_display_name(name, "rag") == "Search Agent"

    def test_falls_back_to_other_locale_when_target_missing(self, provisioner: OpenWebuiProvisioner) -> None:
        provisioner._settings.MODEL_NAME_LOCALE = "fr"
        name = LocaleStringEntity(de="Such-Agent", en="Search Agent")

        # fr missing -> platform default locale (de) before any other available translation
        assert provisioner._resolve_display_name(name, "rag") == "Such-Agent"

    def test_falls_back_to_agent_id_when_all_empty(self, provisioner: OpenWebuiProvisioner) -> None:
        provisioner._settings.MODEL_NAME_LOCALE = "en"
        name = LocaleStringEntity()

        assert provisioner._resolve_display_name(name, "rag") == "rag"


_RAG_MODEL_ID = "aihub-pipeline.rag.default"


def _managed_row(model_id: str, name: str) -> dict:
    """A row already synced by a prior run of this provisioner — carries the current defaults."""
    return {
        "id": model_id,
        "name": name,
        "meta": {AIHUB_MANAGED_META_KEY: True},
        "params": {"function_calling": "legacy"},
    }


class TestComputeModelDiff:
    def test_compute_models_to_create(self) -> None:
        online = [_RAG_AGENT]
        existing: dict[str, dict] = {}

        to_create, to_update, to_delete = OpenWebuiProvisioner._compute_model_diff(online, existing)

        assert len(to_create) == 1
        assert to_create[0] == _RAG_AGENT
        assert to_update == []
        assert to_delete == set()

    def test_compute_models_to_delete(self) -> None:
        online: list[OnlineAgent] = []
        existing = {_RAG_MODEL_ID: {"id": _RAG_MODEL_ID, "name": "RAG Agent"}}

        to_create, to_update, to_delete = OpenWebuiProvisioner._compute_model_diff(online, existing)

        assert to_create == []
        assert to_update == []
        assert to_delete == {_RAG_MODEL_ID}

    def test_compute_models_unchanged(self) -> None:
        online = [_RAG_AGENT]
        existing = {_RAG_MODEL_ID: _managed_row(_RAG_MODEL_ID, "RAG Agent")}

        to_create, to_update, to_delete = OpenWebuiProvisioner._compute_model_diff(online, existing)

        assert to_create == []
        assert to_update == []
        assert to_delete == set()

    def test_compute_models_to_update_on_rename(self) -> None:
        online = [_RAG_AGENT]
        existing = {_RAG_MODEL_ID: _managed_row(_RAG_MODEL_ID, "Old Name")}

        to_create, to_update, to_delete = OpenWebuiProvisioner._compute_model_diff(online, existing)

        assert to_create == []
        assert to_update == [_RAG_AGENT]
        assert to_delete == set()

    def test_compute_models_to_update_on_function_calling_drift(self) -> None:
        """A row synced before this provisioner started setting function_calling (or under a
        different value) must be reconciled even though its name never changed — see issue #240:
        without this, a changed default here would silently never reach an already-synced row."""
        online = [_RAG_AGENT]
        existing = {_RAG_MODEL_ID: {"id": _RAG_MODEL_ID, "name": "RAG Agent"}}  # no params at all

        to_create, to_update, to_delete = OpenWebuiProvisioner._compute_model_diff(online, existing)

        assert to_create == []
        assert to_update == [_RAG_AGENT]
        assert to_delete == set()


class TestSyncWorkspaceModels:
    @pytest.mark.asyncio
    async def test_sync_creates_workspace_model_for_new_agent(self, provisioner: OpenWebuiProvisioner) -> None:
        mock_client = AsyncMock(spec=httpx.AsyncClient)

        with (
            patch.object(provisioner._openwebui, "list_base_models", return_value=[]) as mock_list,
            patch.object(provisioner._openwebui, "create_model") as mock_create,
            patch.object(provisioner._openwebui, "delete_model") as mock_delete,
        ):
            await provisioner._sync_workspace_models(mock_client, [_RAG_AGENT])

            mock_list.assert_called_once()
            mock_create.assert_called_once()
            create_data = mock_create.call_args[0][1]
            assert create_data["id"] == _RAG_MODEL_ID
            assert "base_model_id" not in create_data
            assert create_data["name"] == "RAG Agent"
            assert create_data["meta"][AIHUB_MANAGED_META_KEY] is True
            assert create_data["params"]["function_calling"] == "legacy"
            mock_delete.assert_not_called()

    @pytest.mark.asyncio
    async def test_sync_deletes_model_for_offline_agent(self, provisioner: OpenWebuiProvisioner) -> None:
        """A stale model still goes, as long as something is online to make 'stale' meaningful."""
        mock_client = AsyncMock(spec=httpx.AsyncClient)

        with (
            patch.object(
                provisioner._openwebui,
                "list_base_models",
                return_value=[
                    _managed_row(_RAG_MODEL_ID, "RAG Agent"),
                    _managed_row("aihub-pipeline.gone.old", "Gone"),
                ],
            ),
            patch.object(provisioner._openwebui, "create_model") as mock_create,
            patch.object(provisioner._openwebui, "delete_model") as mock_delete,
        ):
            await provisioner._sync_workspace_models(mock_client, [_RAG_AGENT])

            mock_create.assert_not_called()
            mock_delete.assert_called_once_with(mock_client, "aihub-pipeline.gone.old")

    @pytest.mark.asyncio
    async def test_sync_skips_deletion_when_no_agent_is_online(self, provisioner: OpenWebuiProvisioner) -> None:
        """An empty online set means agent downtime, not deprovisioning — deleting every model on a
        cold start where the API pod outraces the agent pods would wipe the whole picker."""
        mock_client = AsyncMock(spec=httpx.AsyncClient)

        with (
            patch.object(
                provisioner._openwebui,
                "list_base_models",
                return_value=[
                    _managed_row(_RAG_MODEL_ID, "RAG Agent"),
                    _managed_row("aihub-pipeline.search.default", "Search Agent"),
                ],
            ),
            patch.object(provisioner._openwebui, "create_model") as mock_create,
            patch.object(provisioner._openwebui, "delete_model") as mock_delete,
        ):
            await provisioner._sync_workspace_models(mock_client, [])

            mock_create.assert_not_called()
            mock_delete.assert_not_called()

    @pytest.mark.asyncio
    async def test_sync_updates_model_name_on_rename(self, provisioner: OpenWebuiProvisioner) -> None:
        mock_client = AsyncMock(spec=httpx.AsyncClient)

        with (
            patch.object(
                provisioner._openwebui,
                "list_base_models",
                return_value=[_managed_row(_RAG_MODEL_ID, "Old Name")],
            ),
            patch.object(provisioner._openwebui, "create_model") as mock_create,
            patch.object(provisioner._openwebui, "update_model") as mock_update,
            patch.object(provisioner._openwebui, "delete_model") as mock_delete,
        ):
            await provisioner._sync_workspace_models(mock_client, [_RAG_AGENT])

            mock_create.assert_not_called()
            mock_delete.assert_not_called()
            mock_update.assert_called_once()
            update_data = mock_update.call_args[0][1]
            assert update_data["id"] == _RAG_MODEL_ID
            assert update_data["name"] == "RAG Agent"

    @pytest.mark.asyncio
    async def test_sync_does_not_update_when_name_unchanged(self, provisioner: OpenWebuiProvisioner) -> None:
        mock_client = AsyncMock(spec=httpx.AsyncClient)

        with (
            patch.object(
                provisioner._openwebui,
                "list_base_models",
                return_value=[_managed_row(_RAG_MODEL_ID, "RAG Agent")],
            ),
            patch.object(provisioner._openwebui, "create_model") as mock_create,
            patch.object(provisioner._openwebui, "update_model") as mock_update,
            patch.object(provisioner._openwebui, "delete_model") as mock_delete,
        ):
            await provisioner._sync_workspace_models(mock_client, [_RAG_AGENT])

            mock_create.assert_not_called()
            mock_update.assert_not_called()
            mock_delete.assert_not_called()

    @pytest.mark.asyncio
    async def test_sync_ignores_non_managed_base_rows(self, provisioner: OpenWebuiProvisioner) -> None:
        """A human-created base row (no aihub_managed marker) must survive an agent sync untouched."""
        mock_client = AsyncMock(spec=httpx.AsyncClient)

        with (
            patch.object(
                provisioner._openwebui,
                "list_base_models",
                return_value=[{"id": "aihub-pipeline.custom.123", "name": "Human-made"}],
            ),
            patch.object(provisioner._openwebui, "create_model") as mock_create,
            patch.object(provisioner._openwebui, "delete_model") as mock_delete,
        ):
            await provisioner._sync_workspace_models(mock_client, [])

            mock_create.assert_not_called()
            mock_delete.assert_not_called()

    @pytest.mark.asyncio
    async def test_sync_ignores_managed_llm_rows(self, provisioner: OpenWebuiProvisioner) -> None:
        """An LLM model's managed row must not be mistaken for a stale agent row and deleted."""
        mock_client = AsyncMock(spec=httpx.AsyncClient)

        with (
            patch.object(
                provisioner._openwebui,
                "list_base_models",
                return_value=[_managed_row("text-generation/Kimi-K2.6", "Kimi")],
            ),
            patch.object(provisioner._openwebui, "create_model") as mock_create,
            patch.object(provisioner._openwebui, "delete_model") as mock_delete,
        ):
            await provisioner._sync_workspace_models(mock_client, [_RAG_AGENT])

            mock_create.assert_called_once()
            create_data = mock_create.call_args[0][1]
            assert create_data["id"] == _RAG_MODEL_ID
            mock_delete.assert_not_called()

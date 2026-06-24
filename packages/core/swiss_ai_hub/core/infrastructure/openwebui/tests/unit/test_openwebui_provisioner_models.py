from unittest.mock import AsyncMock, patch

import httpx
import pytest

from swiss_ai_hub.core.infrastructure.openwebui.online_agent import OnlineAgent
from swiss_ai_hub.core.infrastructure.openwebui.openwebui_provisioner import (
    AIHUB_MODEL_PREFIX,
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


_RAG_MODEL_ID = f"{AIHUB_MODEL_PREFIX}rag-default"


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
        existing = {_RAG_MODEL_ID: {"id": _RAG_MODEL_ID, "name": "RAG Agent"}}

        to_create, to_update, to_delete = OpenWebuiProvisioner._compute_model_diff(online, existing)

        assert to_create == []
        assert to_update == []
        assert to_delete == set()

    def test_compute_models_to_update_on_rename(self) -> None:
        online = [_RAG_AGENT]
        existing = {_RAG_MODEL_ID: {"id": _RAG_MODEL_ID, "name": "Old Name"}}

        to_create, to_update, to_delete = OpenWebuiProvisioner._compute_model_diff(online, existing)

        assert to_create == []
        assert to_update == [_RAG_AGENT]
        assert to_delete == set()


class TestSyncWorkspaceModels:
    @pytest.mark.asyncio
    async def test_sync_creates_workspace_model_for_new_agent(self, provisioner: OpenWebuiProvisioner) -> None:
        mock_client = AsyncMock(spec=httpx.AsyncClient)

        with (
            patch.object(provisioner._openwebui, "list_models", return_value=[]) as mock_list,
            patch.object(provisioner._openwebui, "create_model") as mock_create,
            patch.object(provisioner._openwebui, "delete_model") as mock_delete,
        ):
            await provisioner._sync_workspace_models(mock_client, [_RAG_AGENT])

            mock_list.assert_called_once()
            mock_create.assert_called_once()
            create_data = mock_create.call_args[0][1]
            assert create_data["id"] == "aihub-agent-rag-default"
            assert create_data["base_model_id"] == "aihub-pipeline.rag.default"
            assert create_data["name"] == "RAG Agent"
            mock_delete.assert_not_called()

    @pytest.mark.asyncio
    async def test_sync_deletes_model_for_offline_agent(self, provisioner: OpenWebuiProvisioner) -> None:
        mock_client = AsyncMock(spec=httpx.AsyncClient)

        with (
            patch.object(
                provisioner._openwebui,
                "list_models",
                return_value=[{"id": "aihub-agent-rag-default"}],
            ),
            patch.object(provisioner._openwebui, "create_model") as mock_create,
            patch.object(provisioner._openwebui, "delete_model") as mock_delete,
        ):
            await provisioner._sync_workspace_models(mock_client, [])

            mock_create.assert_not_called()
            mock_delete.assert_called_once_with(mock_client, "aihub-agent-rag-default")

    @pytest.mark.asyncio
    async def test_sync_updates_model_name_on_rename(self, provisioner: OpenWebuiProvisioner) -> None:
        mock_client = AsyncMock(spec=httpx.AsyncClient)

        with (
            patch.object(
                provisioner._openwebui,
                "list_models",
                return_value=[{"id": "aihub-agent-rag-default", "name": "Old Name"}],
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
            assert update_data["id"] == "aihub-agent-rag-default"
            assert update_data["name"] == "RAG Agent"

    @pytest.mark.asyncio
    async def test_sync_does_not_update_when_name_unchanged(self, provisioner: OpenWebuiProvisioner) -> None:
        mock_client = AsyncMock(spec=httpx.AsyncClient)

        with (
            patch.object(
                provisioner._openwebui,
                "list_models",
                return_value=[{"id": "aihub-agent-rag-default", "name": "RAG Agent"}],
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
    async def test_sync_ignores_non_aihub_models(self, provisioner: OpenWebuiProvisioner) -> None:
        mock_client = AsyncMock(spec=httpx.AsyncClient)

        with (
            patch.object(
                provisioner._openwebui,
                "list_models",
                return_value=[{"id": "custom-model-123"}],
            ),
            patch.object(provisioner._openwebui, "create_model") as mock_create,
            patch.object(provisioner._openwebui, "delete_model") as mock_delete,
        ):
            await provisioner._sync_workspace_models(mock_client, [])

            mock_create.assert_not_called()
            mock_delete.assert_not_called()

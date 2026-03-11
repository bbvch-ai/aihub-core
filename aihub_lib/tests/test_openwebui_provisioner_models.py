from unittest.mock import AsyncMock, patch

import httpx
import pytest

from aihub_lib.infrastructure.openwebui.OpenWebuiProvisioner import (
    AIHUB_MODEL_PREFIX,
    OpenWebuiProvisioner,
)


class TestComputeModelDiff:
    def test_compute_models_to_create(self) -> None:
        online = [("rag", "default", "RAG Agent")]
        existing: set[str] = set()

        to_create, to_delete = OpenWebuiProvisioner._compute_model_diff(online, existing)

        assert len(to_create) == 1
        assert to_create[0] == ("rag", "default", "RAG Agent")
        assert to_delete == set()

    def test_compute_models_to_delete(self) -> None:
        online: list[tuple[str, str, str]] = []
        existing = {f"{AIHUB_MODEL_PREFIX}rag-default"}

        to_create, to_delete = OpenWebuiProvisioner._compute_model_diff(online, existing)

        assert to_create == []
        assert to_delete == {f"{AIHUB_MODEL_PREFIX}rag-default"}

    def test_compute_models_unchanged(self) -> None:
        online = [("rag", "default", "RAG Agent")]
        existing = {f"{AIHUB_MODEL_PREFIX}rag-default"}

        to_create, to_delete = OpenWebuiProvisioner._compute_model_diff(online, existing)

        assert to_create == []
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
            await provisioner._sync_workspace_models(mock_client, [("rag", "default", "RAG Agent")])

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

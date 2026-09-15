from unittest.mock import AsyncMock, patch

import httpx
import pytest

from swiss_ai_hub.core.infrastructure.openwebui.available_model import AvailableModel
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

# A row already synced by a prior run of *this* provisioner — every field it manages carries its
# current desired value, so a diff against it must find nothing to update unless a test deliberately
# perturbs one field.
_SYNCED_META = {AIHUB_MANAGED_META_KEY: True, "capabilities": {"web_search": False}}
_SYNCED_PARAMS = {"function_calling": "legacy"}

# A row the workspace has its own opinions about: a human-set profile image, an unmanaged
# capability (vision), an unmanaged param (temperature), and a stale value for the one capability
# AI-Hub does manage (web_search) — everything here except web_search must survive an update.
_WORKSPACE_OWNED = {
    "id": _RAG_MODEL_ID,
    "name": "RAG Agent",
    "meta": {
        "description": "AI-Hub agent: rag/default",
        "profile_image_url": "/cache/image/rag.png",
        AIHUB_MANAGED_META_KEY: True,
        "capabilities": {"web_search": True, "vision": True},
    },
    "params": {"temperature": 0.2, "function_calling": "legacy"},
}


def _managed_row(model_id: str, name: str, **overrides: object) -> dict:
    """A row already synced by a prior run of this provisioner — carries the current defaults.

    ``overrides`` replaces top-level keys (e.g. ``meta={...}``) for a test that needs one field to
    look stale while keeping every other managed field correctly synced, so the drift it's exercising
    stays isolated from the other two ``_compute_model_diff`` now also checks.
    """
    row = {"id": model_id, "name": name, "meta": dict(_SYNCED_META), "params": dict(_SYNCED_PARAMS)}
    row.update(overrides)
    return row


class TestAgentCapabilities:
    def test_web_search_is_off_for_agents(self) -> None:
        """OpenWebUI drops web-search hits before they reach the pipe, so the toggle must not render."""
        assert OpenWebuiProvisioner._agent_capabilities()["web_search"] is False

    def test_agent_model_carries_the_capabilities(self, provisioner: OpenWebuiProvisioner) -> None:
        model_data = provisioner._build_model_data(_RAG_AGENT)

        assert model_data["meta"]["capabilities"] == {"web_search": False}

    def test_llm_model_keeps_web_search(self, provisioner: OpenWebuiProvisioner) -> None:
        """Plain LLM models bypass the pipe, so OpenWebUI's own web search works for them."""
        model_data = provisioner._build_llm_model_data(
            AvailableModel(capability="text-generation", name="gemma", display_name="gemma")
        )

        assert "capabilities" not in model_data["meta"]


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
        different value) must be reconciled even though nothing else drifted — see issue #240:
        without this, a changed default here would silently never reach an already-synced row."""
        online = [_RAG_AGENT]
        existing = {_RAG_MODEL_ID: _managed_row(_RAG_MODEL_ID, "RAG Agent", params={})}  # no params at all

        to_create, to_update, to_delete = OpenWebuiProvisioner._compute_model_diff(online, existing)

        assert to_create == []
        assert to_update == [_RAG_AGENT]
        assert to_delete == set()

    def test_compute_models_to_update_when_capabilities_missing(self) -> None:
        """Models provisioned before the capability existed carry no meta and must be back-filled,
        even though nothing else drifted."""
        online = [_RAG_AGENT]
        existing = {_RAG_MODEL_ID: _managed_row(_RAG_MODEL_ID, "RAG Agent", meta={})}

        to_create, to_update, to_delete = OpenWebuiProvisioner._compute_model_diff(online, existing)

        assert to_create == []
        assert to_update == [_RAG_AGENT]
        assert to_delete == set()

    def test_compute_models_to_update_when_capability_flipped(self) -> None:
        online = [_RAG_AGENT]
        existing = {
            _RAG_MODEL_ID: _managed_row(_RAG_MODEL_ID, "RAG Agent", meta={"capabilities": {"web_search": True}})
        }

        to_create, to_update, to_delete = OpenWebuiProvisioner._compute_model_diff(online, existing)

        assert to_update == [_RAG_AGENT]

    def test_compute_models_ignores_capabilities_we_do_not_manage(self) -> None:
        """An admin toggling vision in the OpenWebUI workspace must not trigger an endless update loop."""
        online = [_RAG_AGENT]
        existing = {
            _RAG_MODEL_ID: _managed_row(
                _RAG_MODEL_ID, "RAG Agent", meta={"capabilities": {"web_search": False, "vision": True}}
            )
        }

        to_create, to_update, to_delete = OpenWebuiProvisioner._compute_model_diff(online, existing)

        assert to_update == []


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
            assert create_data["meta"]["capabilities"] == {"web_search": False}
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
        stored = _managed_row(_RAG_MODEL_ID, "Old Name")

        with (
            patch.object(provisioner._openwebui, "list_base_models", return_value=[stored]),
            patch.object(provisioner._openwebui, "get_model", return_value=stored),
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
    async def test_sync_backfills_capabilities_on_existing_model(self, provisioner: OpenWebuiProvisioner) -> None:
        """The name and function-calling mode are untouched, so only the missing capability can pull
        this model into the update pass."""
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        # meta keeps the managed marker (or list_base_models' own filter would drop this row as
        # unmanaged and route it through create instead) but omits capabilities specifically.
        stored = _managed_row(_RAG_MODEL_ID, "RAG Agent", meta={AIHUB_MANAGED_META_KEY: True})

        with (
            patch.object(provisioner._openwebui, "list_base_models", return_value=[stored]),
            patch.object(provisioner._openwebui, "get_model", return_value=stored),
            patch.object(provisioner._openwebui, "update_model") as mock_update,
        ):
            await provisioner._sync_workspace_models(mock_client, [_RAG_AGENT])

            mock_update.assert_called_once()
            assert mock_update.call_args[0][1]["meta"]["capabilities"] == {"web_search": False}

    @pytest.mark.asyncio
    async def test_sync_keeps_what_the_workspace_owns(self, provisioner: OpenWebuiProvisioner) -> None:
        """``/models/model/update`` writes every column, so an update must carry the stored fields
        back — a human-set profile image, an unmanaged capability, an unmanaged param — while still
        overriding the one capability (web_search) this provisioner does manage."""
        mock_client = AsyncMock(spec=httpx.AsyncClient)

        with (
            patch.object(provisioner._openwebui, "list_base_models", return_value=[_WORKSPACE_OWNED]),
            patch.object(provisioner._openwebui, "get_model", return_value=_WORKSPACE_OWNED),
            patch.object(provisioner._openwebui, "update_model") as mock_update,
        ):
            await provisioner._sync_workspace_models(mock_client, [_RAG_AGENT])

            update_data = mock_update.call_args[0][1]
            assert update_data["meta"]["profile_image_url"] == "/cache/image/rag.png"
            assert update_data["params"]["temperature"] == 0.2
            assert update_data["params"]["function_calling"] == "legacy"
            assert update_data["meta"]["capabilities"] == {"web_search": False, "vision": True}

    @pytest.mark.asyncio
    async def test_sync_does_not_update_when_nothing_drifted(self, provisioner: OpenWebuiProvisioner) -> None:
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

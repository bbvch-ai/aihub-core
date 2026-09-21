"""Tests for OpenWebuiProvisioner — LLM model provisioning (issue #1450)."""

from contextlib import contextmanager
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from scim2_models import Group

from swiss_ai_hub.core.infrastructure.openwebui.access_grant import AccessGrant
from swiss_ai_hub.core.infrastructure.openwebui.available_model import AvailableModel
from swiss_ai_hub.core.infrastructure.openwebui.openwebui_provisioner import (
    AIHUB_LLM_MODEL_PREFIX,
    AIHUB_MANAGED_META_KEY,
    OpenWebuiProvisioner,
)

_GEMMA = AvailableModel(capability="text-generation", name="gemma-4-31B-it", display_name="gemma-4-31B-it")
_GEMMA_ID = f"{AIHUB_LLM_MODEL_PREFIX}text-generation-gemma-4-31B-it"
_GEMMA_LLM_ID = _GEMMA.litellm_name


def _managed_row(model_id: str, name: str) -> dict:
    """A row already synced by a prior run of this provisioner — carries the current defaults."""
    return {
        "id": model_id,
        "name": name,
        "meta": {AIHUB_MANAGED_META_KEY: True},
        "params": {"function_calling": "legacy"},
    }


def _group(display_name: str, group_id: str) -> Group:
    g = Group(display_name=display_name)
    g.id = group_id
    return g


@contextmanager
def _litellm_returning(entries: list[dict]):
    """Stubs LiteLLMProxySettings().httpx_aclient so _get_available_llm_models sees ``entries``."""
    response = MagicMock()
    response.raise_for_status = MagicMock()
    response.json.return_value = {"data": entries}

    client = AsyncMock()
    client.get = AsyncMock(return_value=response)
    client.__aenter__ = AsyncMock(return_value=client)
    client.__aexit__ = AsyncMock(return_value=False)

    settings = MagicMock()
    settings.httpx_aclient = client
    with patch(
        "swiss_ai_hub.core.infrastructure.openwebui.openwebui_provisioner.LiteLLMProxySettings",
        return_value=settings,
    ):
        yield


class TestGetAvailableLlmModels:
    @pytest.mark.asyncio
    async def test_keeps_only_chat_models(self, provisioner: OpenWebuiProvisioner) -> None:
        with _litellm_returning(
            [
                {"model_name": "text-generation/gemma-4-31B-it", "model_info": {"mode": "chat"}},
                {"model_name": "embedding/bge-m3", "model_info": {"mode": "embedding"}},
                {"model_name": "reranker/bge", "model_info": {"mode": "rerank"}},
            ]
        ):
            models = await provisioner._get_available_llm_models()

        assert [m.litellm_name for m in models] == ["text-generation/gemma-4-31B-it"]
        assert models[0].capability == "text-generation"
        assert models[0].name == "gemma-4-31B-it"

    @pytest.mark.asyncio
    async def test_skips_bare_name_without_capability(self, provisioner: OpenWebuiProvisioner) -> None:
        with _litellm_returning([{"model_name": "barename", "model_info": {"mode": "chat"}}]):
            models = await provisioner._get_available_llm_models()

        assert models == []


class TestBuildLlmModelData:
    def test_registers_raw_id_with_no_base_model_id(self, provisioner: OpenWebuiProvisioner) -> None:
        data = provisioner._build_llm_model_data(_GEMMA)

        assert data["id"] == "text-generation/gemma-4-31B-it"
        assert "base_model_id" not in data
        assert data["name"] == "gemma-4-31B-it"
        assert data["meta"][AIHUB_MANAGED_META_KEY] is True
        assert data["params"]["function_calling"] == "legacy"


class TestSyncLlmWorkspaceModels:
    @pytest.mark.asyncio
    async def test_creates_model_for_new_llm(self, provisioner: OpenWebuiProvisioner) -> None:
        mock_client = AsyncMock(spec=httpx.AsyncClient)

        with (
            patch.object(provisioner._openwebui, "list_base_models", return_value=[]),
            patch.object(provisioner._openwebui, "create_model") as mock_create,
            patch.object(provisioner._openwebui, "delete_model") as mock_delete,
        ):
            await provisioner._sync_llm_workspace_models(mock_client, [_GEMMA])

            mock_create.assert_called_once()
            create_data = mock_create.call_args[0][1]
            assert create_data["id"] == _GEMMA_LLM_ID
            assert "base_model_id" not in create_data
            mock_delete.assert_not_called()

    @pytest.mark.asyncio
    async def test_deletes_orphaned_llm_model(self, provisioner: OpenWebuiProvisioner) -> None:
        mock_client = AsyncMock(spec=httpx.AsyncClient)

        with (
            patch.object(
                provisioner._openwebui, "list_base_models", return_value=[_managed_row(_GEMMA_LLM_ID, "gemma-4-31B-it")]
            ),
            patch.object(provisioner._openwebui, "create_model") as mock_create,
            patch.object(provisioner._openwebui, "delete_model") as mock_delete,
        ):
            await provisioner._sync_llm_workspace_models(mock_client, [])

            mock_create.assert_not_called()
            mock_delete.assert_called_once_with(mock_client, _GEMMA_LLM_ID)

    @pytest.mark.asyncio
    async def test_updates_name_on_drift(self, provisioner: OpenWebuiProvisioner) -> None:
        mock_client = AsyncMock(spec=httpx.AsyncClient)

        with (
            patch.object(provisioner._openwebui, "list_base_models", return_value=[_managed_row(_GEMMA_LLM_ID, "Old")]),
            patch.object(provisioner._openwebui, "create_model") as mock_create,
            patch.object(provisioner._openwebui, "update_model") as mock_update,
            patch.object(provisioner._openwebui, "delete_model") as mock_delete,
        ):
            await provisioner._sync_llm_workspace_models(mock_client, [_GEMMA])

            mock_create.assert_not_called()
            mock_delete.assert_not_called()
            mock_update.assert_called_once()
            assert mock_update.call_args[0][1]["name"] == "gemma-4-31B-it"

    @pytest.mark.asyncio
    async def test_no_update_when_name_unchanged(self, provisioner: OpenWebuiProvisioner) -> None:
        mock_client = AsyncMock(spec=httpx.AsyncClient)

        with (
            patch.object(
                provisioner._openwebui,
                "list_base_models",
                return_value=[_managed_row(_GEMMA_LLM_ID, "gemma-4-31B-it")],
            ),
            patch.object(provisioner._openwebui, "create_model") as mock_create,
            patch.object(provisioner._openwebui, "update_model") as mock_update,
            patch.object(provisioner._openwebui, "delete_model") as mock_delete,
        ):
            await provisioner._sync_llm_workspace_models(mock_client, [_GEMMA])

            mock_create.assert_not_called()
            mock_update.assert_not_called()
            mock_delete.assert_not_called()

    @pytest.mark.asyncio
    async def test_updates_row_synced_before_function_calling_default_existed(
        self, provisioner: OpenWebuiProvisioner
    ) -> None:
        """A row synced before this provisioner started setting function_calling (or under a
        different value) must be reconciled even though its name never changed — see issue #240:
        without this, a changed default here would silently never reach an already-synced row."""
        mock_client = AsyncMock(spec=httpx.AsyncClient)

        with (
            patch.object(
                provisioner._openwebui,
                "list_base_models",
                return_value=[{"id": _GEMMA_LLM_ID, "name": "gemma-4-31B-it", "meta": {AIHUB_MANAGED_META_KEY: True}}],
            ),
            patch.object(provisioner._openwebui, "create_model") as mock_create,
            patch.object(provisioner._openwebui, "update_model") as mock_update,
            patch.object(provisioner._openwebui, "delete_model") as mock_delete,
        ):
            await provisioner._sync_llm_workspace_models(mock_client, [_GEMMA])

            mock_create.assert_not_called()
            mock_delete.assert_not_called()
            mock_update.assert_called_once()
            assert mock_update.call_args[0][1]["params"]["function_calling"] == "legacy"

    @pytest.mark.asyncio
    async def test_ignores_agent_pipe_rows(self, provisioner: OpenWebuiProvisioner) -> None:
        """A managed agent-pipe row must not be deleted by the LLM sync (different id shape)."""
        mock_client = AsyncMock(spec=httpx.AsyncClient)

        with (
            patch.object(
                provisioner._openwebui,
                "list_base_models",
                return_value=[_managed_row("aihub-pipeline.rag.default", "RAG Agent")],
            ),
            patch.object(provisioner._openwebui, "create_model") as mock_create,
            patch.object(provisioner._openwebui, "delete_model") as mock_delete,
        ):
            await provisioner._sync_llm_workspace_models(mock_client, [])

            mock_create.assert_not_called()
            mock_delete.assert_not_called()

    @pytest.mark.asyncio
    async def test_ignores_non_managed_base_rows(self, provisioner: OpenWebuiProvisioner) -> None:
        """A human-created base row (no aihub_managed marker) must not be deleted by the LLM sync."""
        mock_client = AsyncMock(spec=httpx.AsyncClient)

        with (
            patch.object(
                provisioner._openwebui,
                "list_base_models",
                return_value=[{"id": "text-generation/some-custom-model", "name": "Human-made"}],
            ),
            patch.object(provisioner._openwebui, "create_model") as mock_create,
            patch.object(provisioner._openwebui, "delete_model") as mock_delete,
        ):
            await provisioner._sync_llm_workspace_models(mock_client, [])

            mock_create.assert_not_called()
            mock_delete.assert_not_called()


class TestParseLlmFromModel:
    def test_parses_capability_and_name(self) -> None:
        model = {"id": "text-generation/gemma-4-31B-it"}
        assert OpenWebuiProvisioner._parse_llm_from_model(model) == ("text-generation", "gemma-4-31B-it")

    def test_returns_none_without_slash(self) -> None:
        model = {"id": "no-slash"}
        assert OpenWebuiProvisioner._parse_llm_from_model(model) is None

    def test_returns_none_for_empty_id(self) -> None:
        assert OpenWebuiProvisioner._parse_llm_from_model({}) is None


class TestComputeAccessForLlmModel:
    def test_group_with_matching_rules_gets_access(self) -> None:
        groups = [_group("aihub:T1:R1", "grp-1")]
        tenant_rules = {"T1": ["aihub.user.model.text-generation.*"]}
        role_rules = {("T1", "R1"): ["aihub.user.model.text-generation.*"]}

        result = OpenWebuiProvisioner._compute_access_for_llm_model(
            "text-generation", "gemma-4-31B-it", groups, tenant_rules, role_rules
        )

        assert result == [AccessGrant(principal_type="group", principal_id="grp-1", permission="read")]

    def test_other_capability_denied(self) -> None:
        groups = [_group("aihub:T1:R1", "grp-1")]
        tenant_rules = {"T1": ["aihub.user.model.embedding.*"]}
        role_rules = {("T1", "R1"): ["aihub.user.model.embedding.*"]}

        result = OpenWebuiProvisioner._compute_access_for_llm_model(
            "text-generation", "gemma-4-31B-it", groups, tenant_rules, role_rules
        )

        assert result == []

    def test_tenant_ceiling_blocks_role_access(self) -> None:
        groups = [_group("aihub:T1:R1", "grp-1")]
        tenant_rules = {"T1": ["aihub.user.model.embedding.*"]}
        role_rules = {("T1", "R1"): ["aihub.user.model.text-generation.*"]}

        result = OpenWebuiProvisioner._compute_access_for_llm_model(
            "text-generation", "gemma-4-31B-it", groups, tenant_rules, role_rules
        )

        assert result == []

    def test_wildcard_grants_broad_access(self) -> None:
        groups = [_group("aihub:T1:R1", "grp-1")]
        tenant_rules = {"T1": ["aihub.user.model.>"]}
        role_rules = {("T1", "R1"): ["aihub.user.model.>"]}

        result = OpenWebuiProvisioner._compute_access_for_llm_model(
            "text-generation", "gemma-4-31B-it", groups, tenant_rules, role_rules
        )

        assert result == [AccessGrant(principal_type="group", principal_id="grp-1", permission="read")]

    def test_non_aihub_and_malformed_groups_skipped(self) -> None:
        groups = [
            _group("custom-group", "grp-custom"),
            _group("aihub:only-one-part", "grp-bad"),
            _group("aihub:T1:R1", "grp-good"),
        ]
        tenant_rules = {"T1": ["aihub.user.model.>"]}
        role_rules = {("T1", "R1"): ["aihub.user.model.>"]}

        result = OpenWebuiProvisioner._compute_access_for_llm_model(
            "text-generation", "gemma-4-31B-it", groups, tenant_rules, role_rules
        )

        assert [g.principal_id for g in result] == ["grp-good"]


class TestComputeGrantsForManagedModel:
    """Dispatch is by id shape now — a managed row carries no base_model_id hop to key off."""

    def test_dispatches_llm_model_to_model_access(self, provisioner: OpenWebuiProvisioner) -> None:
        groups = [_group("aihub:T1:R1", "grp-1")]
        tenant_rules = {"T1": ["aihub.user.model.>"]}
        role_rules = {("T1", "R1"): ["aihub.user.model.>"]}
        model = {"id": _GEMMA_LLM_ID}

        result = provisioner._compute_grants_for_managed_model(model, groups, tenant_rules, role_rules)

        assert result == [AccessGrant(principal_type="group", principal_id="grp-1", permission="read")]

    def test_dispatches_agent_model_to_agent_access(self, provisioner: OpenWebuiProvisioner) -> None:
        groups = [_group("aihub:T1:R1", "grp-1")]
        tenant_rules = {"T1": ["aihub.user.agent.>"]}
        role_rules = {("T1", "R1"): ["aihub.user.agent.>"]}
        model = {"id": "aihub-pipeline.rag.default"}

        result = provisioner._compute_grants_for_managed_model(model, groups, tenant_rules, role_rules)

        assert result == [AccessGrant(principal_type="group", principal_id="grp-1", permission="read")]

    def test_bare_id_returns_none(self, provisioner: OpenWebuiProvisioner) -> None:
        model = {"id": "custom-model-123"}
        assert provisioner._compute_grants_for_managed_model(model, [], {}, {}) is None

    def test_malformed_agent_pipe_id_returns_none(self, provisioner: OpenWebuiProvisioner) -> None:
        model = {"id": "aihub-pipeline.nodot"}
        assert provisioner._compute_grants_for_managed_model(model, [], {}, {}) is None


class TestSyncAccessGrantsLlm:
    @pytest.mark.asyncio
    async def test_sets_grants_on_llm_model(self, provisioner: OpenWebuiProvisioner) -> None:
        mock_client = AsyncMock(spec=httpx.AsyncClient)

        with (
            patch.object(
                provisioner._openwebui,
                "list_base_models",
                return_value=[_managed_row(_GEMMA_LLM_ID, "gemma-4-31B-it")],
            ),
            patch.object(provisioner._openwebui, "list_groups", return_value=[_group("aihub:T1:R1", "grp-1")]),
            patch.object(provisioner._openwebui, "update_model_access") as mock_update,
            patch(
                "swiss_ai_hub.core.infrastructure.openwebui.openwebui_provisioner.TenantMetadataEntity"
            ) as mock_tenant,
            patch("swiss_ai_hub.core.infrastructure.openwebui.openwebui_provisioner.RoleEntity") as mock_role,
        ):
            tenant = MagicMock()
            tenant.id = "T1"
            tenant.name = "T1"
            tenant.access_rules = ["aihub.user.model.>"]
            mock_tenant.objects.return_value = [tenant]

            role = MagicMock()
            role.name = "R1"
            role.tenant_id = "T1"
            role.access_rules = ["aihub.user.model.text-generation.*"]
            mock_role.objects.return_value = [role]

            await provisioner._sync_access_grants(mock_client)

            mock_update.assert_called_once()
            assert mock_update.call_args[0][1] == _GEMMA_LLM_ID
            grants = mock_update.call_args[0][2]
            assert AccessGrant(principal_type="group", principal_id="grp-1", permission="read") in grants
